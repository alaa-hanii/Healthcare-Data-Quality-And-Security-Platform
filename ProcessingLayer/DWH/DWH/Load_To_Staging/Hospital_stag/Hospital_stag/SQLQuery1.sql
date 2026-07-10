select * from [dbo].[MEDICAL_HISTORY_STG];     -- done   kbh
select * from [dbo].[EQUIPMENT_STG];           -- done
select * from [dbo].[DOCTORS_STG];             -- done
select * from [dbo].[NOTIFICATIONS_STG];       -- done
select * from [dbo].[ADMISSIONS_STG];         -- done
select * from [dbo].[APPOINTMENTS_STG];       -- done
select * from [dbo].[BEDS_STG];               -- done
select * from [dbo].[DEPARTMENTS_STG];        -- done
select * from [dbo].[NURSES_STG];              -- done
select * from [dbo].[PATIENTS_STG];           -- done
select * from [dbo].[ROOMS_STG];



ALTER TABLE [dbo].[notifications_secured]
ALTER COLUMN appointment_id int;

ALTER TABLE [dbo].[NURSES_STG]
ALTER COLUMN PHONE nvarchar (50);

add name nvarchar(50);

select * from [dbo].[NURSES_STG];

ALTER TABLE [dbo].[BEDS_STG]
ALTER COLUMN  BED_NUM nvarchar(50);


ALTER TABLE [dbo].[departments_secured]
ALTER COLUMN department_id int;

ALTER TABLE [dbo].[PATIENTS_STG]
ALTER COLUMN NATIONAL_ID NVARCHAR(150);

ALTER COLUMN FIRST_NAME NVARCHAR(50);

ALTER TABLE [dbo].[ROOMS_STG]
ALTER COLUMN STATUS NVARCHAR(50);





