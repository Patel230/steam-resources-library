CREATE TABLE `reviewer_queue` (
	`id` int AUTO_INCREMENT NOT NULL,
	`submitterName` varchar(160) NOT NULL,
	`submitterEmail` varchar(320) NOT NULL,
	`country` varchar(120) NOT NULL,
	`resourceUrl` varchar(2048) NOT NULL,
	`resourceTitle` varchar(255) NOT NULL,
	`sourceType` varchar(96) NOT NULL,
	`notes` text,
	`status` enum('pending','researching','approved','rejected') NOT NULL DEFAULT 'pending',
	`submittedAt` timestamp NOT NULL DEFAULT (now()),
	`reviewedAt` timestamp,
	`reviewerId` int,
	`reviewerNotes` text,
	CONSTRAINT `reviewer_queue_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `users` (
	`id` int AUTO_INCREMENT NOT NULL,
	`openId` varchar(64) NOT NULL,
	`name` text,
	`email` varchar(320),
	`loginMethod` varchar(64),
	`role` enum('user','admin') NOT NULL DEFAULT 'user',
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	`lastSignedIn` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `users_id` PRIMARY KEY(`id`),
	CONSTRAINT `users_openId_unique` UNIQUE(`openId`)
);
--> statement-breakpoint
ALTER TABLE `reviewer_queue` ADD CONSTRAINT `reviewer_queue_reviewerId_users_id_fk` FOREIGN KEY (`reviewerId`) REFERENCES `users`(`id`) ON DELETE set null ON UPDATE no action;