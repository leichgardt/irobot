cmd = """-- Table: irobot.support

-- DROP TABLE IF EXISTS irobot.support;

CREATE TABLE IF NOT EXISTS irobot.support
(
    support_id bigint NOT NULL DEFAULT nextval('irobot.support_support_id_seq'::regclass),
    chat_id bigint NOT NULL,
    opened timestamp(0) without time zone NOT NULL DEFAULT now(),
    closed timestamp(0) without time zone,
    read boolean NOT NULL DEFAULT false,
    oper_id smallint,
    rating smallint,
    CONSTRAINT support_pkey PRIMARY KEY (support_id, chat_id),
    CONSTRAINT "Обращения" UNIQUE (support_id),
    CONSTRAINT operator FOREIGN KEY (oper_id)
        REFERENCES irobot.operators (oper_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS irobot.support
    OWNER to postgres;

COMMENT ON TABLE irobot.support
    IS 'Таблица обращений в поддержку';
"""