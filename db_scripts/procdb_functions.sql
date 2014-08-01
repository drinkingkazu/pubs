--Overwrite functions if they already exist

---------------------------------------------------------------------
--/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/--
---------------------------------------------------------------------

--Homemade types
DROP TYPE IF EXISTS RunSubrunList CASCADE;

---------------------------------------------------------------------
--/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/--
---------------------------------------------------------------------
--Create a Project table with columns: Run, Subrun, Status, Seq
DROP FUNCTION IF EXISTS MakeProjTable(TEXT);
CREATE OR REPLACE FUNCTION MakeProjTable(myName TEXT) RETURNS INT AS $$
DECLARE
--local variables can go here
myQuery   TEXT;
startTime TIMESTAMP;
rec1      RECORD;
rec2      RECORD;
BEGIN

  IF DoesTableExist(myName) THEN
    RAISE EXCEPTION 'Project table % already exists.',myName;
  ELSE
    myQuery := format('CREATE TABLE %s ( Run        INT       NOT NULL,
    	       		      	       	 SubRun     INT       NOT NULL,
					 Seq        SMALLINT  NOT NULL DEFAULT 0,
					 ProjectVer SMALLINT  NOT NULL DEFAULT 0,
					 Status     SMALLINT  NOT NULL DEFAULT 1,
					 Data       TEXT DEFAULT NULL,
					 PRIMARY KEY (Run,SubRun,Seq,ProjectVer))',myName);
    EXECUTE myQuery;
    -- insert defaul set of runs
    SELECT StartRun, StartSubRun FROM ProcessTable WHERE Project = myName ORDER BY ProjectVer DESC LIMIT 1 INTO rec1;
    FOR rec2 IN SELECT RunNumber, SubRunNumber FROM MainRun 
    	       WHERE RunNumber > rec1.StartRun 
    	       OR (RunNumber = rec1.StartRun AND SubRunNumber > rec1.StartSubRun) LOOP
      myQuery := format('INSERT INTO %s (Run,SubRun) VALUES (%s,%s)',myName,rec2.RunNumber,rec2.SubRunNumber);
      EXECUTE myQuery;
    END LOOP;
  END IF;
    
RETURN 1;  	
END;
$$ LANGUAGE PLPGSQL;

---------------------------------------------------------------------
--/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/--
---------------------------------------------------------------------
--Insert a new row into a project table.
--The added row will have a sequence number = 0 and version is taken from the ProcessTable
--Returns 0 upon success.
DROP FUNCTION IF EXISTS InsertIntoProjTable(TEXT,INT,INT);

CREATE OR REPLACE FUNCTION InsertIntoProjTable( tname    TEXT,
       	  	  	   			myrun    INT,
						mysubrun INT
						 ) RETURNS INT AS $$
DECLARE
myQuery TEXT;
myBool  BOOLEAN;
current_ver SMALLINT;
BEGIN
  --make sure table exists  
  IF NOT DoesTableExist(tname) THEN
    RAISE EXCEPTION 'Table % does not exist.', tname;
  END IF;

  --no negative values in this table
  IF myrun < 0 OR mysubrun < 0 THEN
    RAISE EXCEPTION 'Can''t have negative values in table %.', tname;
  END IF;

  --check to make sure run/subrun is not already in table
  myQuery := format('(SELECT TRUE FROM %s WHERE Run = %s AND SubRun = %s)',tname,myrun,mysubrun);
  EXECUTE myQuery INTO myBool;
  IF NOT myBool IS NULL THEN
    RAISE EXCEPTION 'Table % already has Run=% and SubRun=%',tname,myrun,mysubrun;
  END IF;

  --get current version number of the project
  SELECT MAX(ProjectVer) FROM ProcessTable WHERE Project = tname INTO current_ver;
  IF current_ver IS NULL THEN
    RAISE EXCEPTION 'Project % is not found in ProcessTable!',tname;
  END IF;

  myQuery := format('INSERT INTO %s (run,subrun,version) VALUES (%s,%s,%s)',tname,myrun,mysubrun,current_ver);
  EXECUTE myQuery;
  
  RETURN 0;

END;
$$ LANGUAGE PLPGSQL;

---------------------------------------------------------------------
--/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/--
---------------------------------------------------------------------
--Increase # of sequences for a specified run/subrun number (version taken from ProcessTable).
--Status is set to 1 by default (i.e. same status as master scheduler's insertion of a new run)
DROP FUNCTION IF EXISTS IncreaseProjSequence(TEXT,INT,INT,SMALLINT,SMALLINT);
CREATE OR REPLACE FUNCTION IncreaseProjSequence( tname  TEXT,
       	  	  	   		    	 run    INT,
					    	 subrun INT,
					    	 nseq   SMALLINT,
					    	 status SMALLINT DEFAULT 1) RETURNS INT AS $$
DECLARE
current_ver SMALLINT;
myQuery  TEXT;
myMaxSeq INT;
myRecord RECORD;
BEGIN
  --make sure table exists  
  IF NOT DoesTableExist(tname) THEN
    RAISE EXCEPTION 'Table % does not exist.', tname;
  END IF;

  --no negative values in this table
  IF run < 0 OR subrun < 0 OR nseq < 0 OR status < 0 THEN
    RAISE EXCEPTION 'Can''t have negative values in table %.', tname;
  END IF;

  --check to make sure run/subrun is not already in table
  myQuery := format('(SELECT MAX(ProjectVer) FROM %s WHERE Run = %s AND SubRun = %s)',tname,run,subrun);
  EXECUTE myQuery INTO current_ver;

  IF current_ver IS NULL THEN
    RAISE EXCEPTION 'Project % has no (Run,SubRun) = (%,%)',tname,run,subrun;
  END IF;

  myQuery := format('SELECT MAX(Seq) FROM %s WHERE Run = %s AND SubRun = %s AND ProjectVer = %s',tname,run,subrun,current_ver);
  EXECUTE myQuery INTO myMaxSeq;
  IF myMaxSeq >= nseq THEN
    RAISE EXCEPTION 'Project % (Run,SubRun) = (%,%) already contains % sequences (requested = %!)',tname,run,subrun,myMaxSeq,nseq;
  END IF;

  myMaxSeq := myMaxSeq + 1;

  FOR seq IN myMaxSeq..(nseq-1) LOOP
    myQuery := format('INSERT INTO %s (Run,SubRun,Seq,ProjectVer,Status) VALUES (%s,%s,%s,%s,%s)',tname,run,subrun,seq,current_ver,status);
    EXECUTE myQuery;
  END LOOP;
  RETURN 0;  

END;
$$ LANGUAGE PLPGSQL;

---------------------------------------------------------------------
--/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/--
---------------------------------------------------------------------
--Update status entry in an existing row of Project table
DROP FUNCTION IF EXISTS UpdateProjStatus(TEXT,INT,INT,SMALLINT,SMALLINT);
CREATE OR REPLACE FUNCTION UpdateProjStatus( tname TEXT, 
       	  	  	   		     myrun INT, 
					     mysubrun INT,
					     myseq SMALLINT,
					     mystatus SMALLINT ) RETURNS VOID AS $$
DECLARE
dummy TEXT;
local_version INT;
BEGIN

  --make sure table exists  
  IF NOT DoesTableExist(tname) THEN
    RAISE EXCEPTION 'Table % does not exist.', tname;
  END IF;

  --check if row exists in table
  dummy := format('SELECT MAX(ProjectVer) FROM %s WHERE run = %s AND subrun = %s AND seq = %s',tname,myrun,mysubrun,myseq);
  EXECUTE dummy INTO local_version;

  IF local_version IS NULL THEN
    RAISE EXCEPTION 'Project % has no (run,subrun,seq) = (%,%,%)!',tname,myrun,mysubrun,myseq;
  ELSE
    dummy := format('UPDATE ONLY %s SET status = %s WHERE run = %s AND subrun = %s AND seq = %s AND ProjectVer = %s',tname,mystatus,myrun,mysubrun,myseq,local_version);
    EXECUTE dummy;
  END IF;

  RETURN ;
END;
$$ LANGUAGE PLPGSQL;

---------------------------------------------------------------------
--/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/--
---------------------------------------------------------------------

--DROP TYPE IF EXISTS ProjectID CASCADE;
--CREATE TYPE ProjectID AS (Run INT, SubRun INT, Seq SMALLINT, ProjectVer SMALLINT);
DROP FUNCTION IF EXISTS GetRuns(project_name TEXT,status INT);
CREATE OR REPLACE FUNCTION GetRuns ( project_name TEXT,
       	    	       	   	     status       INT 
				   ) RETURNS TABLE (Run INT, SubRun INT, Seq SMALLINT, ProjectVer SMALLINT) AS $$
DECLARE
  query   TEXT;
  rec     RECORD;
--  res_row ProjectID;
BEGIN
  IF NOT DoesTableExist(project_name) THEN
    RAISE EXCEPTION 'Project % does not exist!',project_name;
  END IF;

  query := format(' SELECT %s.Run, %s.SubRun, %s.Seq, %s.ProjectVer FROM 
  	   	    %s JOIN ( SELECT Run,SubRun,Seq,MAX(ProjectVer) AS ProjectVer FROM %s WHERE Status=%s GROUP BY Run,SubRun,Seq ) AS FOO
		    ON %s.Run = FOO.Run AND %s.SubRun=FOO.SubRun AND %s.Seq=FOO.Seq AND %s.ProjectVer=FOO.ProjectVer ORDER BY FOO.Run, 
		    FOO.SubRun, FOO.Seq',
		  project_name,
		  project_name,
		  project_name,
		  project_name,
		  project_name,
		  project_name,
		  status,
		  project_name,
		  project_name,
		  project_name,
		  project_name);
  FOR rec IN EXECUTE query LOOP
    RETURN QUERY SELECT rec.Run,
    	   	 	rec.SubRun,
			rec.Seq,
			Rec.ProjectVer;
  END LOOP;

END;
$$ LANGUAGE PLPGSQL;

---------------------------------------------------------------------
--/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/--
---------------------------------------------------------------------
--This function looks at all project tables supplied arrayOfTables, 
--and for each project table you ask for a specific status supplied in arrayOfStatuses.
--The function returns the run/subrun #s when each project has that respective status
--ALSO REQUIRING that ALL sequence numbers for that run/subrun have that status
--IE ALL of the jobs (sequences) need to be finished for this function to return
--that run and subrun number

DROP FUNCTION IF EXISTS GetRuns(TEXT[],SMALLINT[]);

CREATE OR REPLACE FUNCTION GetRuns( arrayOfTables TEXT[], 
    	  	  	   	    arrayOfStatuses SMALLINT[]) RETURNS TABLE (Run INT, SubRun INT) AS $$
DECLARE
iTable          TEXT;
dummy           TEXT;
dummyTableName  TEXT;
myRecord        RECORD;
loopCounter     INT;
myInt           INT;
myversion       SMALLINT;
version_v       SMALLINT[];
vrr             RECORD;
BEGIN

  --make sure all of the tables exist
  FOREACH iTable IN ARRAY arrayOfTables LOOP
    IF NOT DoesTableExist(iTable) THEN
      RAISE EXCEPTION 'Table % does not exist.', iTable;
    END IF;
    SELECT Max(ProjectVer) FROM ProcessTable WHERE Project = iTable INTO myversion;
    IF myversion IS NULL THEN
      RAISE EXCEPTION 'ProjectVer number not found for project % (something is terribly wrong)!',iTable;
    END IF;
    version_v := version_v || myversion;
  END LOOP;

  --each table needs its own status, so the two input arrays need to be the same length
  IF array_length(arrayOfTables,1) != array_length(arrayOfStatuses,1) THEN
    RAISE EXCEPTION 'Your input tables array is different length than input status array.';
  END IF;

  --create a temporary table for each table, then INNER JOIN them to get end result
  --[1] is the first element in psql, not [0]!  
  loopCounter := 1;
  FOREACH iTable IN ARRAY arrayOfTables LOOP
    dummyTableName := 'temp'||iTable;
    dummy := format(' CREATE TEMPORARY TABLE %s (RUN INT, SUBRUN INT, PRIMARY KEY (RUN,SUBRUN));',dummyTableName);
    EXECUTE dummy;
    FOR vrr IN SELECT * FROM GetVersionRunRange(arrayOfTables[loopCounter]) LOOP
      dummy := format(' INSERT INTO %s ( SELECT Run, SubRun FROM 
      	       		       	       	 ( SELECT DISTINCT RUN,SUBRUN,COUNT(SEQ) AS SEQ_COUNT, SUM(STATUS) AS STATUS_SUM FROM
					   %s WHERE ProjectVer = %s AND ( (RUN > %s AND RUN < %s) OR (Run = %s AND SubRun >= %s ) OR
					   (Run = %s AND SubRun < %s) ) GROUP BY RUN, SUBRUN 
					  ) AS FOO WHERE SEQ_COUNT*%s = STATUS_SUM
					)',
		      dummyTableName,
		      arrayOfTables[loopCounter],
		      vrr.ProjectVer,
		      vrr.StartRun,
		      vrr.EndRun,
		      vrr.StartRun,
		      vrr.StartSubRun,
		      vrr.EndRun,
		      vrr.EndSubRun,
		      arrayOfStatuses[loopCounter]
		      );
      RAISE INFO '%',dummy;
      EXECUTE dummy;

    END LOOP;
    dummy := format('SELECT COUNT(Run) FROM %s',dummyTableName);
    EXECUTE dummy INTO myInt;
    IF myInt IS NULL OR myInt = 0 THEN
      FOR index IN 1..loopCounter LOOP
        dummyTableName := 'temp'||index;
        dummy := format('DROP TABLE IF EXISTS %s',dummyTableName);
        EXECUTE dummy;
      END LOOP;
      RETURN;
    END IF;

    loopCounter := loopCounter + 1;
  END LOOP;
 
  --now do the inner joining:
  --build a query to inner join each table with the first to get the end result.
  --dummy := format('SELECT * FROM %s','temp'||arrayOfTables[1]);
  dummy := 'SELECT * FROM temp'||arrayOfTables[1];
  loopCounter := 1;
  FOREACH iTable IN ARRAY arrayOfTables LOOP
    --skip the first temporary table... don't need to INNER JOIN it with itself
    IF iTable = arrayOfTables[1] THEN 
      loopCounter := loopCounter + 1; 
      CONTINUE;
    END IF;
    dummy := format('%s INNER JOIN %s ON %s.run = %s.run AND %s.subrun = %s.subrun',dummy,'temp'||iTable,'temp'||iTable,'temp'||iTable,'temp'||iTable,'temp'||iTable,'temp'||iTable);

    loopCounter := loopCounter + 1;
  END LOOP;
  dummy := format('%s ORDER BY temp%s.Run, temp%s.SubRun',dummy,arrayOfTables[1],arrayOfTables[1]);

  --debug: print the actual query you're doing
  --RAISE INFO '%',dummy;
 
  FOR myRecord IN EXECUTE dummy LOOP
    RETURN QUERY SELECT myRecord.run AS RUN, myRecord.subrun AS SUBRUN;
    --RETURN NEXT myRecord;
  END LOOP;


  --drop all of the temporary tables... this is dangerous! don't drop the actual tables...
  FOREACH iTable IN ARRAY arrayOfTables LOOP
    dummy := 'DROP TABLE IF EXISTS temp'||iTable;
    EXECUTE dummy;
  END LOOP;
  RETURN;
END;
$$ LANGUAGE PLPGSQL;