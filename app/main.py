import asyncio
from json import loads
import logging
from os.path import dirname, abspath
from random import choice
from signal import signal, SIGINT, SIGTERM
from sqlalchemy import create_engine, text
import ssl
from websockets import connect, ConnectionClosed, InvalidURI

from .settings import settings


# ----------------------------------------------------------------------------
# Create table if it does not exist
def create_table():
    global connection

    # Check if table is created
    created = connection.execute(text(
        "SELECT EXISTS ("\
        " SELECT 1 FROM information_schema.tables"\
        " WHERE table_name = 'impacts');"
    ))
    created = created.fetchone()
    created = created[0]
    if created:
        return False

    # Create the table
    with open(dirname(abspath(__file__)) + '/init.sql') as fd:
        query = " ".join([line.rstrip("\n") for line in fd])
    connection.execute(text(query))
    connection.commit()
    return True

# ----------------------------------------------------------------------------
# Decompress payload received by websocket using LZW algo
def decompress(b):
    e = {}
    d = list(b)
    c = d[0]
    f = c
    g = [c]
    h = 256
    o = h
    for b in range(1, len(d)):
        a = ord(d[b])
        a = d[b] if h > a else e.get(a, f + c)
        g.append(a)
        c = a[0]
        e[o] = f + c
        o += 1
        f = a
    return "".join(g)

# ----------------------------------------------------------------------------
# Insert a new impact into the database
def add_impact(ts, lat, lon):
    global connection

    connection.execute(text(
        "INSERT INTO impacts (ts, lat, lon, location) VALUES (" + \
            str(ts) + "," + str(lat*10000000) + "," + str(lon*10000000) + \
            ",ll_to_earth(" + str(lat) + "," + str(lon) + ")" + \
        ") ON CONFLICT DO NOTHING;"
    ))
    # connection.commit()

# ----------------------------------------------------------------------------
# Remove impacts older then 12 hours from database
def del_old_impact():
    global connection

    result = connection.execute(text(
        'DELETE FROM impacts WHERE ts < ' + \
        '(EXTRACT(epoch FROM NOW()) - 60 * 60 * 12) * 1000000000;'
    ))
    # connection.commit()
    logging.info('DELETED impacts: %i', result.rowcount)

# ----------------------------------------------------------------------------
# Message handling procedure (get from websocket and put in database)
async def handle_messages(ws):
    while True:
        try:
            msg = await asyncio.wait_for(
                ws.recv(),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logging.info('Server timeouted')
            break
        try:
            data = loads(decompress(msg))
            impact = {
                'ts': int(data['time']),
                'lat': float(data['lat']),
                'lon': float(data['lon']),
            }
            del msg, data
        except Exception:
            logging.exception('Exception during unpacking:')
        logging.debug('Got (%i, %f, %f)', impact['ts'], impact['lat'], impact['lon'])
        add_impact(**impact)

# ----------------------------------------------------------------------------
# Main task (choose and open websocket)
async def main():
    logging.info('Start service')

    # Basic TLS setup
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    hosts = ["ws1", "ws3", "ws5", "ws7", "ws8"]

    while True:
        del_old_impact()
        try:
            uri = "wss://{}.blitzortung.org:443/".format(choice(hosts))
            logging.info("Server selected: %s", uri)
            async with connect(
                uri,
                ssl=ssl_context,
                open_timeout=2.0,
                close_timeout=1.0
            ) as websocket:
                logging.info('Connected to server %s', uri)
                await websocket.send('{"a": 111}')
                await handle_messages(websocket)
        except ConnectionClosed:
            logging.info('Connection closed with server %s', uri)
        except InvalidURI:
            logging.info('Server %s failed', uri)
        except Exception:
            logging.exception('Exception in Loop:')

# ----------------------------------------------------------------------------
# Signal handler
def sig_handler(signum=None, frame=None):
    raise KeyboardInterrupt()

# ----------------------------------------------------------------------------
if __name__ == '__main__':
    # Connect to the database
    engine = create_engine(
        'postgresql://{}:{}@{}:{}/{}'.format(
            settings.postgres_user,
            settings.postgres_password,
            settings.postgres_host,
            settings.postgres_port,
            settings.postgres_database
        )
    )
    connection = engine.connect()
    if settings.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    logging.info("Connected to db")

    if create_table():
        logging.info("Initializing database")
    else:
        logging.info("Database already initialized")

    signal(SIGINT, sig_handler)
    signal(SIGTERM, sig_handler)

    # Run main task
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Exiting')
    except Exception:
        logging.exception('Exception in main:')

    connection.close()
    engine.dispose()
