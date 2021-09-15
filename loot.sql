CREATE TABLE "operations" (
	"operation_id"	INTEGER NOT NULL,
	"operation_name"	TEXT NOT NULL UNIQUE,
	"operation_description"	TEXT,
	"alert_level"	INTEGER NOT NULL DEFAULT 100,
	PRIMARY KEY("operation_id")
)
CREATE TABLE "discord" (
	"discord_id"	INTEGER NOT NULL,
	"server_id"	INTEGER NOT NULL UNIQUE,
	"operation_id"	INTEGER NOT NULL,
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON DELETE CASCADE,
	PRIMARY KEY("discord_id")
);
CREATE TABLE "reddit" (
	"reddit_id"	INTEGER NOT NULL,
	"subreddit"	TEXT NOT NULL UNIQUE,
	"operation_id"	INTEGER NOT NULL,
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON DELETE CASCADE,
	PRIMARY KEY("reddit_id")
);
CREATE TABLE "users" (
	"user_id"	INTEGER NOT NULL,
	"username"	TEXT NOT NULL,
	"website"	TEXT NOT NULL,
	"source"	TEXT NOT NULL,
	"hash_id"	TEXT NOT NULL UNIQUE,
	"operation_id"	INTEGER NOT NULL,
	"is_target" INTEGER NOT NULL DEFAULT 0,
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON DELETE CASCADE,
	PRIMARY KEY("user_id")
);
CREATE TABLE "watch_list" (
	"watch_id"	INTEGER NOT NULL,
	"word"	TEXT NOT NULL UNIQUE,
	"operation_id"	INTEGER NOT NULL,
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON DELETE CASCADE,
	PRIMARY KEY("watch_id")
);
CREATE TABLE "messages" (
	"message_id"	INTEGER NOT NULL,
	"message"	TEXT NOT NULL,
	"date"	TEXT NOT NULL,
	"watch_id"	INTEGER,
	"hash_id"	TEXT UNIQUE,
	"source"	INTEGER,
	FOREIGN KEY("source") REFERENCES "users"("user_id") ON DELETE CASCADE,
	PRIMARY KEY("message_id"),
	FOREIGN KEY("watch_id") REFERENCES "watch_list"("watch_id") ON DELETE CASCADE
);
CREATE TABLE "loot" (
	"loot_id"	INTEGER NOT NULL,
	"data"	TEXT NOT NULL,
	"source"	TEXT,
	"type"	TEXT NOT NULL,
	"date"	TEXT NOT NULL,
	"hash_id"	INTEGER UNIQUE,
	"operation_id"	INTEGER,
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON DELETE CASCADE,
	PRIMARY KEY("loot_id")
);
CREATE TABLE "telegram" (
	"telegram_id"	INTEGER NOT NULL,
	"operation_id"	INTEGER NOT NULL,
	"name"	TEXT NOT NULL,
	"chan_id"	INTEGER NOT NULL UNIQUE,
	PRIMARY KEY("telegram_id"),
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON DELETE CASCADE
);
CREATE TABLE "twitter" (
	"twitter_uid"	INTEGER NOT NULL,
	"username"	TEXT NOT NULL UNIQUE,
	"operation_id"	INTEGER NOT NULL,
	"source"	TEXT DEFAULT "user",
	FOREIGN KEY("operation-id") REFERENCES "operations"("operation_id") ON DELETE CASCADE,
	PRIMARY KEY("twitter_uid")
);
CREATE TABLE "telegram_bots" (
	"id"	INTEGER,
	"api_id"	INTEGER NOT NULL UNIQUE,
	"api_hash"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("id")
);
CREATE TABLE "discord_bots" (
	"id"	INTEGER NOT NULL,
	"token"	TEXT UNIQUE,
	PRIMARY KEY("id")
)
CREATE TABLE "rss" (
	"operation_id"	INTEGER,
	"url"	TEXT UNIQUE,
	"feed_id"	INTEGER NOT NULL,
	PRIMARY KEY("feed_id"),
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON DELETE CASCADE
)
CREATE TABLE "crawler" (
	"url"	TEXT NOT NULL UNIQUE,
	"domain"	TEXT NOT NULL,
	"update"	INTEGER NOT NULL DEFAULT 0,
	"source"	TEXT,
	"crawl_id"	INTEGER,
	"operation_id"	INTEGER,
	"cookie"	TEXT,
	"username"	TEXT,
	"email"	TEXT,
	"password"	TEXT,
	"last_update"	TEXT,
	"send_alets"	INTEGER NOT NULL DEFAULT 0,
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON DELETE CASCADE,
	PRIMARY KEY("crawl_id")
)
