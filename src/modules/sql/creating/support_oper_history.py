cmd = """-- Table: irobot.support_oper_history

-- DROP TABLE IF EXISTS irobot.support_oper_history;

CREATE TABLE IF NOT EXISTS irobot.support_oper_history
(
    support_id bigint NOT NULL,
    oper_id smallint NOT NULL,
    datetime timestamp without time zone NOT NULL DEFAULT now(),
    operation character(6) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT "Обращения" FOREIGN KEY (support_id)
        REFERENCES irobot.support (support_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT "Операторы" FOREIGN KEY (oper_id)
        REFERENCES irobot.operators (oper_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS irobot.support_oper_history
    OWNER to postgres;

COMMENT ON TABLE irobot.support_oper_history
    IS 'История оказания поддержки операторами (по времени)';
"""