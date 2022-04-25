cmd = """-- Table: irobot.subs

-- DROP TABLE IF EXISTS irobot.subs;

CREATE TABLE IF NOT EXISTS irobot.subs
(
    chat_id bigint NOT NULL,
    datetime timestamp(0) without time zone NOT NULL DEFAULT now(),
    inline_msg_id integer,
    subscribed boolean NOT NULL DEFAULT false,
    mailing boolean NOT NULL DEFAULT true,
    inline_text text COLLATE pg_catalog."default",
    notify boolean NOT NULL DEFAULT true,
    inline_parse_mode character(16) COLLATE pg_catalog."default",
    hash character(128) COLLATE pg_catalog."default",
    userdata jsonb,
    support_mode boolean NOT NULL DEFAULT false,
    username character(32) COLLATE pg_catalog."default",
    first_name character(32) COLLATE pg_catalog."default",
    last_name character(32) COLLATE pg_catalog."default",
    photo character(128) COLLATE pg_catalog."default",
    CONSTRAINT subs_pkey PRIMARY KEY (chat_id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS irobot.subs
    OWNER to postgres;

COMMENT ON TABLE irobot.subs
    IS 'Таблица чатов пользователей (абонентов)';

COMMENT ON COLUMN irobot.subs.inline_msg_id
    IS 'Message_id последнего сообщения с inline клавиатурой';

COMMENT ON COLUMN irobot.subs.subscribed
    IS 'Флаг, подписан ли абонент к боту';

COMMENT ON COLUMN irobot.subs.mailing
    IS 'Флаг новостной рассылки';

COMMENT ON COLUMN irobot.subs.inline_text
    IS 'Текст inline сообщения';

COMMENT ON COLUMN irobot.subs.notify
    IS 'Флаг рассылки уведомлений';

COMMENT ON COLUMN irobot.subs.inline_parse_mode
    IS 'Parse_mode последнего inline сообщения';

COMMENT ON COLUMN irobot.subs.hash
    IS 'Хэш, используемый для авторизации в боте (происходит через веб-страницу)';

COMMENT ON COLUMN irobot.subs.userdata
    IS 'Telegram данные пользователя';

COMMENT ON COLUMN irobot.subs.support_mode
    IS 'Флаг режима поддержки';

COMMENT ON COLUMN irobot.subs.photo
    IS 'Ссылка на аватар';
"""