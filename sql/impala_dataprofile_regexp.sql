-- Script created by Benjamin Grauer

-- Script designed for Impala to identify/bucket different types of data w/ regular expressions.  Each time I work with a new dataset, I add to the script.
--  You can swap out the test fields sub-query with real fields in a database to generalize what types of data you are working with (example at bottom)
--  it can then be wrapped in code to iterate through each field of a table/view, and you quickly ramp-up and get a feel for what type of data is present.
--   usefull for situations where you are trying to learn the data types of a data set quickly
--  the "d" prefix means real data, "nd" means non-data category.
--  The inner sub-query must convert/cast to a string for the rest to work properly

-- Next Adds when time permits:
--  check for 00/00/0000, check for "%", word "year" for text year, category with year numbers, category with 3-mo sub-setted, 

SELECT
    data_field,
    CASE
        -- null / blank strings
        WHEN data_field IS NULL THEN ('nd(null)')
        WHEN LENGTH(data_field) >= 1 AND LENGTH(regexp_replace(data_field, '\\s+', '')) = 0 THEN 'nd(blank spaces)'
        WHEN trim(data_field) = '' THEN 'nd(blank)'
        
        -- dates
        WHEN LENGTH(regexp_extract(data_field, '^[0-0]{4}-(0[0-0]|1[0-0])-(0[0-0]|[0-0][0-0]|3[0-0])$', 0)) = 10 THEN 'nd(Date 0000-00-00)'    -- must be before the zero check
        WHEN LENGTH(regexp_extract(TRIM(data_field), '^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])$', 0)) > 0 THEN 'd(Date YYYY-MM-DD)'
        WHEN LENGTH(regexp_extract(regexp_replace(TRIM(data_field), '\/', '-'), '^(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])-[0-9]{4}$' ,0)) > 0 THEN 'd(Date MM/DD/YYYY)'   -- have to convert this to dashes first

        -- zeros
        WHEN regexp_replace(TRIM(CAST(data_field AS STRING)), '0+((\.0+)|(-0+)*)', '') = '' THEN 'nd(all zeros)'

        -- dollar / decimal amounts
        WHEN regexp_replace(TRIM(data_field), '^[0-9]*$', '') = '' THEN 'd(all numeric)'
        WHEN LENGTH(regexp_extract(TRIM(data_field), '^[\$+-]?[0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?$', 0)) > 0 THEN 'd(curr/dec amt)' -- test
        WHEN CAST(data_field AS DECIMAL(18,4)) < 0 THEN 'd(negative num)'

        -- Need a decimal to catch any non-dollar amounts
        WHEN LENGTH(regexp_extract(TRIM(data_field), '^[0-9]*(?:\.[0-9]*)?$', 0)) > 0 THEN 'd(decimal)' 
        
        -- alpha / numerics
        WHEN regexp_replace(TRIM(data_field), '[A-Za-z]', '') = '' THEN 'd(all alpha)'
        WHEN trim(data_field) <> '' THEN 'd(populated)'
        
        ELSE 'n/a'
        END as data_profile_type,
        testdesc
FROM
(
    -- Nulls / Blank / Blank Spaces
    SELECT 1.1 as rowcol, null as data_field, 'null test' as testdesc
    UNION
    SELECT 1.2 as rowcol, '' as data_field, 'blank string' as testdesc
    UNION
    SELECT 1.3 as rowcol, '     ' as data_field, 'blank spaces' as testdesc
    UNION

    -- All Zeros
    SELECT 2.1 as rowcol, '00000' as data_field, 'all zeros' as testdesc
    UNION
    SELECT 2.2 as rowcol, '0.00' as data_field, 'zero dollar amounts' as testdesc
    UNION

    -- Dates
    SELECT 3.1 as rowcol, '0000-00-00' as data_field, 'date 0`s (yyyy-mm-dd)' as testdesc
    UNION
    SELECT 3.2 as rowcol, '0000-00-00  ' as data_field, 'date 0`s (yyyy-mm-dd) w/spaces' as testdesc
    UNION
    SELECT 3.3 as rowcol, '1945-01-10' as data_field, 'date (yyyy-mm-dd)' as testdesc
    UNION
    SELECT 3.4 as rowcol, '12/31/1945' as data_field, 'date (mm/dd/yyyy)' as testdesc

    -- Dollar / Decimal Amounts
    UNION
    SELECT 4.1 as rowcol, '.' as data_field, 'single period' as testdesc
    UNION
    SELECT 4.2 as rowcol, '1.25' as data_field, 'dollar / decimal' as testdesc
    UNION
    SELECT 4.3 as rowcol, '1.25 ' as data_field, 'dollar / decimal w/trail spaces' as testdesc
    UNION
    SELECT 4.4 as rowcol, '$1.25' as data_field, 'dollar w/dollar sign' as testdesc
    UNION
    SELECT 4.5 as rowcol, '$1.25 ' as data_field, 'dollar w/dollar sign w/ trail spaces' as testdesc
    UNION
    SELECT 4.6 as rowcol, ' .3 ' as data_field, 'decimal pad/trail spaces' as testdesc
    UNION
    SELECT 4.7 as rowcol, '-3' as data_field, 'negative' as testdesc
    UNION
    SELECT 4.8 as rowcol, '$1,234.56' as data_field, 'dollar thsnd w/sign w/comma' as testdesc
    UNION
    SELECT 4.9 as rowcol, '1,234.56' as data_field, 'dollar thsnd w/comma' as testdesc
    UNION
    SELECT 4.10 as rowcol, '123456.3224' as data_field, 'large decimal (6,4)' as testdesc
    UNION
    SELECT 4.11 as rowcol, '$123,456.3224' as data_field, 'large dollar w/sign (6,4)' as testdesc
    UNION

    -- Alpha / Numeric combinations
    SELECT 5.1 as rowcol, ' 1234567 ' as data_field, 'number with pad/trail spaces' as testdesc
    UNION
    SELECT 5.2 as rowcol, '1234567' as data_field, 'large number' as testdesc
    UNION
    SELECT 5.3 as rowcol, '00001234567' as data_field, 'large num, leading zeros' as testdesc
    UNION
    SELECT 5.4 as rowcol, ' APACHE ' as data_field, 'alpha w/spaces' as testdesc
    UNION
    SELECT 5.5 as rowcol, ' AP123456 ' as data_field, 'alpha-numeric w/spaces' as testdesc
    UNION
    SELECT 5.6 as rowcol, '$1$O3JMY.Tw$AdLnLjQ/5jXF9.MTp3gHv/'  as data_field, 'MD5 hash example' as testdesc

    -- Example of real implementation
    -- SELECT  CAST([field_name] AS STRING) as data_field
    -- FROM [database].[view]
    -- GROUP BY [field_name]

) as a
ORDER BY a.rowcol ASC;