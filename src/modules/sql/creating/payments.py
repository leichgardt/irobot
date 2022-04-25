cmd = """-- Table: irobot.payments

-- DROP TABLE IF EXISTS irobot.payments;

CREATE TABLE IF NOT EXISTS irobot.payments
(
    id bigint NOT NULL DEFAULT nextval('irobot.payments_id_seq'::regclass),
    hash character(128) COLLATE pg_catalog."default" NOT NULL,
    chat_id bigint NOT NULL,
    status character(16) COLLATE pg_catalog."default" DEFAULT 'new'::bpchar,
    datetime timestamp without time zone NOT NULL DEFAULT now(),
    inline bigint,
    agrm character(16) COLLATE pg_catalog."default" NOT NULL,
    amount numeric NOT NULL,
    record_id bigint,
    update_datetime timestamp without time zone,
    payer jsonb,
    receipt character(64) COLLATE pg_catalog."default",
    url character(128) COLLATE pg_catalog."default",
    balance integer,
    CONSTRAINT payments_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE IF EXISTS irobot.payments
    OWNER to postgres;

COMMENT ON TABLE irobot.payments
    IS 'Таблица платежей';

COMMENT ON COLUMN irobot.payments.hash
    IS 'Внутренних хэш платежа, используется для поиска платежа по нему.';

COMMENT ON COLUMN irobot.payments.status
    IS 'new - создан новый счёт для оплаты
processing - оплачено, идёт попытка пополнить баланс
success - баланс пополнен
completed - платёж проверен
warning - провальная проверка
error - ошибка 500
critical - не удалось исправить
canceled -  отменено';

COMMENT ON COLUMN irobot.payments.inline
    IS 'Message_id сообщения со счётом';

COMMENT ON COLUMN irobot.payments.agrm
    IS 'Номер договора для пополнения';

COMMENT ON COLUMN irobot.payments.amount
    IS 'Сумма платежа в рублях';

COMMENT ON COLUMN irobot.payments.record_id
    IS 'ID записи платежа в системе биллинга';

COMMENT ON COLUMN irobot.payments.payer
    IS 'Третий плательщик (если счёт передан для платежа третьим лицам)';

COMMENT ON COLUMN irobot.payments.receipt
    IS 'Номер чека в системе платёжного провайдера (Сбербанк)';

COMMENT ON COLUMN irobot.payments.url
    IS 'Ссылка на оплату через сайт';

COMMENT ON COLUMN irobot.payments.balance
    IS 'Баланс договора до пополнения';
"""