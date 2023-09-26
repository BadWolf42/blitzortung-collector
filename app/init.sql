CREATE EXTENSION IF NOT EXISTS earthdistance CASCADE;
CREATE SEQUENCE impacts_id_seq INCREMENT 1 START 1 CACHE 1;
CREATE TABLE impacts (
    id bigint NOT NULL DEFAULT nextval('impacts_id_seq'::regclass),
    "time" bigint NOT NULL,
    location point NOT NULL,
    CONSTRAINT impacts_pkey PRIMARY KEY (id)
);
ALTER SEQUENCE impacts_id_seq OWNED BY impacts.id;
CREATE INDEX impacts_id on impacts USING btree (id);
CREATE INDEX impacts_loc on impacts USING gist (location);
CREATE INDEX impacts_time on impacts USING btree ("time");
