cmd = """-- Table: irobot.operators

-- DROP TABLE IF EXISTS irobot.operators;

CREATE TABLE IF NOT EXISTS irobot.operators
(
    oper_id smallint NOT NULL DEFAULT nextval('irobot.operators_user_id_seq'::regclass),
    login character(32) COLLATE pg_catalog."default" NOT NULL,
    full_name character(64) COLLATE pg_catalog."default",
    hashed_password character(128) COLLATE pg_catalog."default" NOT NULL,
    datetime timestamp(0) without time zone NOT NULL DEFAULT now(),
    enabled boolean NOT NULL DEFAULT true,
    root boolean NOT NULL DEFAULT false,
    CONSTRAINT operators_pkey PRIMARY KEY (oper_id),
    CONSTRAINT operators_login_key UNIQUE (login)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS irobot.operators
    OWNER to postgres;

COMMENT ON TABLE irobot.operators
    IS 'Таблица операторов';

INSERT INTO irobot.operators (oper_id, login, full_name, hashed_password, root) 
    VALUES (0, 'bot', 'Irobot', '$', true);

INSERT INTO irobot.operators (oper_id, login, full_name, hashed_password, root) 
    VALUES (1, 'admin', 'Администратор',
        'jjruIrkgbPxH$c5f81d5fa56d9962c119c36bb83003b30919abcc7264919c953374979b2233ca', true);
"""