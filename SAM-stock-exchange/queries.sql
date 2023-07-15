--- 1) Creates an external schema access the Glue tables from S3.
create external schema stock_lake
from data catalog
database 'stock-exchange'
iam_role 'arn:aws:iam::XXXXXXXXXXXX:role/RedshiftRoleLab'
create external database if not exists;

--- 2) This query show all tables in the external schema (S3 data lake).
SELECT
  *
FROM
  SVV_EXTERNAL_TABLES
WHERE
  schemaname = 'stock_lake';

--- 3) Count records in the external table.
select count(*) from stock_lake.stock_data;


--- 4) Shows 5 records from the external table.
      select *
      from stock_lake.stock_data
      limit 5;

--- 5) Shows top 10 stocks negotiated by value.
select		ticker, round(sum(price),2) as total_negotiated
from		stock_lake.stock_data
where		status = 'complete'
and			order_type = 'buy'
group by 	ticker
order by 	total_negotiated desc
limit 10;

CREATE MATERIALIZED VIEW stock_trade_by_ticker
AS
select	ticker,
            round(sum(price), 2) as total_negotiated
from		stock_lake.stock_data
where		status = 'complete'
and			order_type = 'buy'
group by 	ticker

---- 6) Shows top 10 investors by value
select		investor_id, round(sum(price),2) as total_negotiated
from		stock_lake.stock_data
where		status = 'complete'
and			order_type = 'buy'
group by 	investor_id
order by 	total_negotiated desc
limit 10;

CREATE MATERIALIZED VIEW stock_trade_by_investor
AS
select	investor_id,
            round(sum(price), 2) as total_negotiated
from		stock_lake.stock_data
where		status = 'complete'
and			order_type = 'buy'
group by 	investor_id


---- 7) Top 10 months by value of the stocks negotiated.
select extract(year from (to_date(order_date, 'YYYY-MM-DD'))) as year,
			 extract(month from (to_date(order_date, 'YYYY-MM-DD'))) as month,
            round(sum(price), 2) as total_price
from		stock_lake.stock_data
where		status = 'complete'
and			order_type = 'buy'
group by 	year, month
order by 	total_price desc
limit 10;


---- 8) Create a materialized view pointing to the external table.
CREATE MATERIALIZED VIEW stock_trade_by_month
SORTKEY (year, month)
AS
select		extract(year from (to_date(order_date, 'YYYY-MM-DD'))) as year,
			extract(month from (to_date(order_date, 'YYYY-MM-DD'))) as month,
            round(sum(price), 2) as total_price
from		stock_lake.stock_data
where		status = 'complete'
and			order_type = 'buy'
group by 	year, month


--- 9) Disable result cache
SET enable_result_cache_for_session TO OFF;

--- 10) Now compare the time to execute the queries bellow.
--- They both returns the same results, but the first query runs faster.
--- This happens because the first query points to the materialized view,
--- where the result is pre computed and is stored in native redshift storage.

--- 10 a) First query, from materialized view.
select		*
from		stock_trade_by_month
order by 	total_price desc;

---- 10 b) Same as query number 7, but from the materialized view.

select year, month, total_price
from		stock_trade_by_month
group by 	year, month, total_price
order by 	total_price desc;