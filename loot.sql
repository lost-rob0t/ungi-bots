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
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON UPDATE CASCADE ON DELETE CASCADE,
	PRIMARY KEY("discord_id")
);
CREATE TABLE "reddit" (
	"reddit_id"	INTEGER NOT NULL,
	"subreddit"	TEXT NOT NULL UNIQUE,
	"operation_id"	INTEGER NOT NULL,
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON UPDATE CASCADE ON DELETE CASCADE,
	PRIMARY KEY("reddit_id")
);
CREATE TABLE "discord_users" (
	"user_id"	INTEGER NOT NULL,
	"usertag"	TEXT NOT NULL UNIQUE,
	"operation_id"	INTEGER NOT NULL,
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON UPDATE CASCADE ON DELETE CASCADE,
	PRIMARY KEY("user_id")
);
CREATE TABLE "reddit_users" (
	"user_id"	INTEGER NOT NULL,
	"username"	TEXT NOT NULL UNIQUE,
	"operation_id"	INTEGER NOT NULL,
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON UPDATE CASCADE ON DELETE CASCADE,
	PRIMARY KEY("user_id")
);
CREATE TABLE "emails" (
	"email_id"	INTEGER NOT NULL,
	"email"	TEXT NOT NULL,
	"operation_id"	INTEGER NOT NULL,
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON UPDATE CASCADE ON DELETE CASCADE,
	PRIMARY KEY("email_id","email")
);
CREATE TABLE "ip" (
	"ip_id"	INTEGER NOT NULL,
	"ip"	TEXT NOT NULL UNIQUE,
	"operation_id"	INTEGER NOT NULL,
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON UPDATE CASCADE ON DELETE CASCADE,
	PRIMARY KEY("ip_id")
);
CREATE TABLE "phone_numbers" (
	"phone_id"	INTEGER NOT NULL,
	"phone"	TEXT,
	"operation_id"	INTEGER,
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON UPDATE CASCADE ON DELETE CASCADE,
	PRIMARY KEY("phone_id")
);
CREATE TABLE "watch_list" (
	"watch_id"	INTEGER NOT NULL,
	"word:"	TEXT NOT NULL UNIQUE,
	"operation_id"	INTEGER NOT NULL,
	FOREIGN KEY("operation_id") REFERENCES "operations"("operation_id") ON UPDATE CASCADE ON DELETE CASCADE,
	PRIMARY KEY("watch_id")
);
CREATE TABLE "watch_output" (
	"output_id"	INTEGER NOT NULL,
	"output"	TEXT NOT NULL,
	"date"	INTEGER NOT NULL,
	"watch_id"	INTEGER NOT NULL,
	FOREIGN KEY("watch_id") REFERENCES "watch_list"("watch_id") ON UPDATE CASCADE ON DELETE CASCADE,
	PRIMARY KEY("output_id")
);

