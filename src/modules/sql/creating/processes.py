cmd = """-- Table: irobot.{name}

-- DROP TABLE IF EXISTS irobot.{name};

CREATE TABLE IF NOT EXISTS irobot.{name}
(
    pid integer NOT NULL,
    tasks character(16)[] COLLATE pg_catalog."default" DEFAULT (ARRAY[]::bpchar[])::character(1)[],
    CONSTRAINT {name}_pkey PRIMARY KEY (pid)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS irobot.{name}
    OWNER to postgres;

COMMENT ON TABLE irobot.{name}
    IS 'Таблица PIDs - Process ID процессов системы';
"""