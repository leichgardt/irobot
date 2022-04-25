cmd = """-- Table: irobot.mailing

-- DROP TABLE IF EXISTS irobot.mailing;

CREATE TABLE IF NOT EXISTS irobot.mailing
(
    id bigint NOT NULL DEFAULT nextval('irobot.mailing_id_seq'::regclass),
    datetime timestamp(0) without time zone NOT NULL DEFAULT now(),
    type character(8) COLLATE pg_catalog."default" NOT NULL,
    text text COLLATE pg_catalog."default" NOT NULL,
    status character(16) COLLATE pg_catalog."default" NOT NULL DEFAULT 'new'::bpchar,
    parse_mode character(8) COLLATE pg_catalog."default",
    targets character(32)[] COLLATE pg_catalog."default",
    CONSTRAINT mailing_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS irobot.mailing
    OWNER to postgres;

COMMENT ON TABLE irobot.mailing
    IS 'Таблица рассылок (новости, уведомления, целевая рассылка)';

COMMENT ON COLUMN irobot.mailing.type
    IS 'direct - для конкретных абонентов
mailing - новостная рассылка, у кого включены новости
notify - уведомительная рассылка для всех';

COMMENT ON COLUMN irobot.mailing.status
    IS 'new - новое сообщение
processing - выполняется
complete - рассылка успешно завершена
missing - не удалось определить цель (target)
error - ошибка 500 (смотрите логи)';

COMMENT ON COLUMN irobot.mailing.parse_mode
    IS 'html, markdown, markdownv2';

COMMENT ON COLUMN irobot.mailing.targets
    IS 'Список целей для рассылки';
"""