cmd = """-- Table: irobot.tokens

-- DROP TABLE IF EXISTS irobot.tokens;

CREATE TABLE IF NOT EXISTS irobot.tokens
(
    token_id smallint NOT NULL DEFAULT nextval('irobot.tokens_token_id_seq'::regclass),
    token uuid NOT NULL DEFAULT uuid_generate_v4(),
    expires timestamp(0) without time zone NOT NULL,
    oper_id smallint NOT NULL,
    CONSTRAINT tokens_pkey PRIMARY KEY (token_id),
    CONSTRAINT "Unique token" UNIQUE (token),
    CONSTRAINT "Operator" FOREIGN KEY (oper_id)
        REFERENCES irobot.operators (oper_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS irobot.tokens
    OWNER to postgres;

COMMENT ON TABLE irobot.tokens
    IS 'Таблица токенов для авторизации операторов.
Для генерирования токенов используется плагин для postgres - uuid-ossp. Для установки выполните запрос:
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"';
"""