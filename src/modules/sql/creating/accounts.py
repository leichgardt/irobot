cmd = """-- Table: irobot.accounts

-- DROP TABLE IF EXISTS irobot.accounts;

CREATE TABLE IF NOT EXISTS irobot.accounts
(
    chat_id bigint NOT NULL,
    login character(16) COLLATE pg_catalog."default" NOT NULL,
    datetime timestamp(0) without time zone NOT NULL DEFAULT now(),
    update_datetime timestamp(0) without time zone,
    active boolean NOT NULL DEFAULT true,
    user_id integer,
    CONSTRAINT accounts_pkey PRIMARY KEY (chat_id, login)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS irobot.accounts
    OWNER to postgres;

COMMENT ON TABLE irobot.accounts
    IS 'Таблица подключенных аккаунтов (договоров) абонентов';
"""