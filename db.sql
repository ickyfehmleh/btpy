CREATE TABLE allowed_trackers (tracker text not null primary key);
CREATE TABLE user_data (hash text, uploaded number, downloaded number, uid number);
CREATE VIEW hashes as select distinct hash from user_data;
CREATE UNIQUE INDEX ud_pk on user_data( hash,uid);
