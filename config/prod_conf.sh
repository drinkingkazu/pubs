# SQL reader account config
export PUB_PSQL_READER_HOST=ifdb01.fnal.gov
export PUB_PSQL_READER_PORT=5437
export PUB_PSQL_READER_USER=$PUB_PROD_ACCOUNT
export PUB_PSQL_READER_ROLE="uboone_admin"
export PUB_PSQL_READER_DB=microboone_dev
export PUB_PSQL_READER_PASS=$PUB_PASS
export PUB_PSQL_READER_CONN_NTRY=10
export PUB_PSQL_READER_CONN_SLEEP=10

# SQL writer account config
export PUB_PSQL_WRITER_HOST=ifdb01.fnal.gov
export PUB_PSQL_WRITER_PORT=5437
export PUB_PSQL_WRITER_USER=$PUB_PROD_ACCOUNT
export PUB_PSQL_WRITER_ROLE="uboone_admin"
export PUB_PSQL_WRITER_DB=microboone_dev
export PUB_PSQL_WRITER_PASS=$PUB_PASS
export PUB_PSQL_WRITER_CONN_NTRY=10
export PUB_PSQL_WRITER_CONN_SLEEP=10

# SQL admin account config
export PUB_PSQL_ADMIN_HOST=ifdb01.fnal.gov
export PUB_PSQL_ADMIN_PORT=5437
export PUB_PSQL_ADMIN_USER=$PUB_PROD_ACCOUNT
export PUB_PSQL_ADMIN_ROLE="uboone_admin"
export PUB_PSQL_ADMIN_DB=microboone_dev
export PUB_PSQL_ADMIN_PASS=$PUB_PASS
export PUB_PSQL_ADMIN_CONN_NTRY=10
export PUB_PSQL_ADMIN_CONN_SLEEP=10

# SMTP account for sending an email report
export PUB_SMTP_ACCT=uboonepro
export PUB_SMTP_SRVR=smtp.gmail.com:587
export PUB_SMTP_PASS=herbgreenlee

#export PUB_SMTP_ACCT=drinkingkazu.pubs@aho.com
#export PUB_SMTP_SRVR=smtp.gmail.com:tako
#export PUB_SMTP_PASS=pubs.drinkingkazuak
