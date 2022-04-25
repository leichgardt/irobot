cmd = """-- Table: irobot.support_messages

-- DROP TABLE IF EXISTS irobot.support_messages;

CREATE TABLE IF NOT EXISTS irobot.support_messages
(
    chat_id bigint NOT NULL,
    message_id integer NOT NULL,
    datetime timestamp(3) without time zone NOT NULL DEFAULT now(),
    from_oper smallint,
    content_type character(16) COLLATE pg_catalog."default" NOT NULL,
    content jsonb NOT NULL,
    read boolean DEFAULT false,
    status character(7) COLLATE pg_catalog."default",
    CONSTRAINT support_messages_pkey PRIMARY KEY (chat_id, message_id),
    CONSTRAINT "Operator" FOREIGN KEY (from_oper)
        REFERENCES irobot.operators (oper_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS irobot.support_messages
    OWNER to postgres;

COMMENT ON TABLE irobot.support_messages
    IS 'Таблица истории сообщений абонента и тех.поддержки';
"""