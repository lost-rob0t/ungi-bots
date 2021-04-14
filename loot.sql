CREATE TABLE "operations" (
	"operation_id"	INTEGER NOT NULL,
	"operation_name"	TEXT NOT NULL UNIQUE,
	"operation_description"	TEXT,
	PRIMARY KEY("operation_id")
);
CREATE TABLE "discord" (
	"discord_id"	INTEGER NOT NULL,
	"server_id"	INTEGER NOT NULL,
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
	"source"	TEXT,
	"hash_id"	TEXT,
	"operation_id"	INTEGER NOT NULL,
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON DELETE CASCADE,
	PRIMARY KEY("user_id")
);
CREATE TABLE "watch_list" (
	"watch_id"	INTEGER NOT NULL,
	"word:"	TEXT NOT NULL UNIQUE,
	"operation_id"	INTEGER NOT NULL,
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON DELETE CASCADE,
	PRIMARY KEY("watch_id")
);
CREATE TABLE "messages" (
	"message_id"	INTEGER NOT NULL,
	"message"	TEXT NOT NULL,
	"date"	TEXT NOT NULL,
	"watch_id"	INTEGER,
	"hash_id"	TEXT UNIQUE
	FOREIGN KEY("watch_id") REFERENCES "watch_list"("watch_id") ON DELETE CASCADE,
	PRIMARY KEY("message_id"),
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON DELETE CASCADE
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
