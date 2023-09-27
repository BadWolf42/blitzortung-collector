CREATE EXTENSION IF NOT EXISTS earthdistance CASCADE;
CREATE SEQUENCE impacts_id_seq AS integer INCREMENT 1 START 1 CACHE 1 CYCLE;

CREATE TABLE impacts (
    id integer NOT NULL DEFAULT nextval('impacts_id_seq'::regclass),
    ts bigint NOT NULL,
    lat integer NOT NULL,
    lon integer NOT NULL,
    location earth NOT NULL,
    CONSTRAINT impacts_pkey PRIMARY KEY (id),
    CONSTRAINT impacts_uniq UNIQUE (lat, lon, ts)
);
ALTER SEQUENCE impacts_id_seq OWNED BY impacts.id;

CREATE INDEX impacts_id ON impacts USING btree (id);
CREATE INDEX impacts_ts ON impacts USING btree (ts);
CREATE INDEX impacts_lat ON impacts USING btree (lat);
CREATE INDEX impacts_lon ON impacts USING btree (lon);
CREATE INDEX impacts_loc ON impacts USING gist (location);
