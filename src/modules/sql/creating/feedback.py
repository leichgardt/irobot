cmd = """-- Table: irobot.feedback

-- DROP TABLE IF EXISTS irobot.feedback;

CREATE TABLE IF NOT EXISTS irobot.feedback
(
    id bigint NOT NULL DEFAULT nextval('irobot.feedback_id_seq'::regclass),
    rating smallint,
    comment text COLLATE pg_catalog."default",
    datetime timestamp(0) without time zone NOT NULL DEFAULT now(),
    chat_id bigint NOT NULL,
    object character(32) COLLATE pg_catalog."default",
    type character(8) COLLATE pg_catalog."default" NOT NULL,
    status character(10) COLLATE pg_catalog."default" NOT NULL DEFAULT 'new'::bpchar,
    update_datetime timestamp(0) without time zone,
    CONSTRAINT feedback_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS irobot.feedback
    OWNER to postgres;

COMMENT ON TABLE irobot.feedback
    IS 'Таблица записей обратной связи (отзывы, оценка заявок Userside).';

COMMENT ON COLUMN irobot.feedback.rating
    IS 'оценка от 1 до 5';

COMMENT ON COLUMN irobot.feedback.object
    IS 'или номер заявки Userside, или оператор, оценка которого была произведена';

COMMENT ON COLUMN irobot.feedback.type
    IS '''feedback'' - обратная связь с заявок Userside
''review'' - отзыв';

COMMENT ON COLUMN irobot.feedback.status
    IS 'Статусы: 
new - новый фидбэк
sending - отправка фидбэка в систему Cardinalis
complete - фидбэк отправлен в систему Cardinalis
passed - Cardinalis отменил фидбэк';
"""