CREATE DATABASE rapido;
USE rapido;

CREATE TABLE rides (
            services VARCHAR(255),
            date DATE,
            time TIME,
            ride_status VARCHAR(255),
            source VARCHAR(255),
            destination VARCHAR(255),
            duration INT,
            ride_id VARCHAR(255) PRIMARY KEY,
            distance FLOAT,
            ride_charge FLOAT DEFAULT NULL,
            misc_charge FLOAT DEFAULT NULL,
            total_fare FLOAT DEFAULT NULL,
            payment_method VARCHAR(255) DEFAULT NULL
        );

SELECT * FROM rides;
---------------------------------------------------------------------------------
---------------------------------------------------------------------------------
/* Basic: */ 
---------------------------------------------------------------------------------
-- 1. Count the total number of rides and completed rides.
SELECT
	COUNT(ride_id) AS Total_Orders,
    SUM(CASE WHEN ride_status = 'COMPLETED' THEN 1 ELSE 0 END) AS Completed_rides_count
FROM rides;
--------------------------------------------------------------------------------------
-- 2. Retrieve unique ride services (`services`) and their total ride count.
SELECT
	services AS Unique_Services,
	COUNT(ride_id) AS Total_Rides
FROM rides
GROUP BY services
ORDER BY Total_Rides DESC;
 --------------------------------------------------------------------------------       
-- 3. Identify the most frequently used payment method.
SELECT
	payment_method AS Popular_payment_method,
    COUNT(payment_method) AS Total_rides
FROM rides 
GROUP BY payment_method
ORDER BY Total_rides DESC
LIMIT 1;
-------------------------------------------------------------------------------------------------
-- 4. Extract rides where `ride_charge` is greater than `total_fare` (possible data error check).
SELECT *
FROM rides
WHERE ride_charge > total_fare;
------------------------------------------------------------------------------------------------------
-- 5. Find the average ride duration by service type.
SELECT
	services,
    ROUND(AVG(duration),1) AS Average_Duration
FROM rides
GROUP BY services
ORDER BY Average_Duration DESC;

-----------------------------------------------------------------------------------
-----------------------------------------------------------------------------------
/* **Intermediate:** */    
-- 6. Identify the busiest day of the week for rides.
SELECT
	DAYNAME(date) AS busiest_day,
    COUNT(ride_id) AS Total_rides
FROM rides
GROUP BY busiest_day
ORDER BY Total_rides DESC
LIMIT 1;
------------------------------------------------------------------------------------
-- 7. Calculate total revenue per month.
SELECT
	MONTH(date) AS Ride_month,
    ROUND( SUM(total_fare),2) AS Total_revenue
FROM rides
GROUP BY Ride_month
ORDER BY Total_revenue DESC;
-----------------------------------------------------------------------------
-- 8. Find the top 5 most common source-destination pairs.
SELECT
	source,
    destination,
	COUNT(ride_id) AS Count
FROM rides
GROUP BY source, destination
ORDER BY Count DESC
LIMIT 5;
--------------------------------------------------------------------------------
-- 9. Calculate the percentage of rides canceled vs. completed.
SELECT
	COUNT(ride_id) AS Total_orders,
	ROUND( SUM(CASE WHEN ride_status = 'completed' THEN 1 ELSE 0 END)  * 100 / COUNT(ride_id) ,2) AS ride_completed_percentage,
    SUM(CASE WHEN ride_status = 'completed' THEN 1 ELSE 0 END) AS Completed_rides_count,
    ROUND( SUM(CASE WHEN ride_status = 'cancelled' THEN 1 ELSE 0 END)  * 100 / COUNT(ride_id) ,2) AS ride_cancelled_percentage,
    SUM(CASE WHEN ride_status = 'cancelled' THEN 1 ELSE 0 END) AS Cancelled_rides_count
FROM rides;
--------------------------------------------------------------------------------------------
-- 10. Identify peak ride hours by analyzing `time` column.
SELECT
	HOUR(time) AS Ride_hour,
    COUNT(ride_id) AS Rides_count
FROM rides
GROUP BY Ride_hour
ORDER BY Rides_count DESC;
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
/* **Advanced:** */
-------------------------------------------------------------------------------
-- 11. Find the longest ride in terms of both **distance** and **duration**.
SELECT *
FROM rides
ORDER BY duration DESC, distance DESC
LIMIT 1;
---------------------------------------------------------------------------------
-- 12. Analyze fare pricing trends by **distance categories** (0-5km, 5-10km, etc.).
WITH Distance_categories AS (
		SELECT 
			CASE
				WHEN distance >0 AND distance <= 5 THEN 'Within 5km (Very short rides)'
				WHEN distance >= 5 AND distance <=10 THEN 'Within 10km (Short rides)'
                WHEN distance >= 10 AND distance <= 20 THEN 'Within 20km (Medium rides)'
                WHEN distance >= 20 AND distance <= 30 THEN 'Within 30km (Above medium rides)'
                WHEN distance > 30 THEN 'More than 30km (Long rides)'
                ELSE 'Ride cancelled'
			END AS Distance_categories,
			ride_charge,
            misc_charge,
            total_fare
		FROM
			rides)
SELECT 
	Distance_categories,
	ROUND( AVG(ride_charge),2) AS Average_base_charge,
	ROUND( AVG(misc_charge),2) AS Average_misc_charge,
	ROUND( AVG(total_fare),2) AS Average_total_charge
FROM Distance_categories
GROUP BY Distance_categories
ORDER BY FIELD(Distance_categories, 
	'Within 5km (Very short rides)',
    'Within 10km (Short Rides)', 
    'Within 20km (Medium Rides)', 
    'Within 30km (Above Medium Rides)', 
    'More than 30km (Long Rides)', 
    'Ride Cancelled');
---------------------------------------------------------------------------------------------------
-- 13. Rank **source-destination** pairs by revenue using window functions.
-- using cte:
WITH sd_pairs AS (
	SELECT
		source,
        destination,
        SUM(total_fare) AS Revenue
    FROM rides
    GROUP BY source, destination)
SELECT 
	source,
    destination,
    ROUND(Revenue,2) AS Revenue,
    DENSE_RANK() OVER (ORDER BY Revenue DESC) AS Source_Destination_Rank
FROM sd_pairs;

-- using sub queries:
SELECT
	source,
    destination,
    ROUND(SUM(total_fare),2) AS Revenue,
    DENSE_RANK() OVER (ORDER BY SUM(total_fare) DESC) AS Source_destination_Rank
FROM rides
GROUP BY source, destination;
---------------------------------------------------------------------------------------------
-- 14. Compare revenue share of different **service types**.
-- using sub query
SELECT
	services AS Services,
    ROUND(SUM(total_fare),2) AS Revenue,
    ROUND(SUM(total_fare)*100 / (SELECT SUM(total_fare) FROM rides), 2) AS Services_revenue_percentage
FROM rides
GROUP BY services
ORDER BY Revenue DESC;
-- using window func:
SELECT
	services AS Services,
    ROUND(SUM(total_fare),2) AS Revenue,
    ROUND(SUM(total_fare)*100.0 / SUM(SUM(total_fare)) OVER(), 2) AS Services_revenue_percentage
FROM rides
GROUP BY services
ORDER BY Revenue DESC;
-----------------------------------------------------------------------------------------------------
-- 15. Create a stored procedure to fetch ride details for a given date range.
DELIMITER //

CREATE PROCEDURE GetRideDetailsByDate(
	IN start_date DATE,
    IN end_date DATE
)
BEGIN 
	SELECT
		ride_id,
        services,
        date,
        time,
        ride_status,
        source,
        destination,
        duration,
        distance,
        ride_charge,
        misc_charge,
        total_fare,
        payment_method
	FROM rides
    WHERE DATE BETWEEN start_date AND end_date
    ORDER BY DATE ASC;
    
END //
DELIMITER ;

CALL GetRideDetailsByDate('2024-01-01', '2024-12-31');
-----------------------------------------------------------------------
-- 16. Identify **low-revenue rides** (low distance, low fare).
WITH Low_Revenue_Rides AS (
    SELECT
        ride_id,
        services,
        source,
        destination,
        date,
        time,
        ride_status,
        duration,
        distance,
        ride_charge,
        misc_charge,
        total_fare,
        payment_method
    FROM rides
    WHERE total_fare <= 75 
      AND distance <= 5 
      AND ride_status = 'completed'
)
SELECT 
    *,
    DENSE_RANK() OVER (ORDER BY total_fare ASC) AS Low_Revenue_Ride_Rank
FROM Low_Revenue_Rides;
---------------------------------------------------------------------------
-- 17. Find seasonal ride trends (compare summer vs. winter).
-- 3. Compare Summer and Winter ride trends:
SELECT
	CASE 
		WHEN MONTH(date) BETWEEN 3 AND 6 THEN 'Summer'
		WHEN MONTH(date) BETWEEN 6 AND 9 THEN 'Monsoon'
        WHEN MONTH(date) BETWEEN 9 AND 12 OR MONTH(date) BETWEEN 1 AND 2 THEN 'Winter'
	END AS Season,
    COUNT(ride_id) AS Total_rides,
    ROUND(SUM(total_fare), 2) AS Total_revenue,
    ROUND(AVG(total_fare), 2) AS Average_fare
FROM rides
GROUP BY Season
-- As per Indian climate and seasons our data is not extended till winter season
;
------------------------------------------------------------------------------------------------
-- 18. Analyze rides with **high misc charges** (potential service issues).

SELECT *
FROM (
    SELECT *,
           ROW_NUMBER() OVER (ORDER BY misc_charge) as rn,
           COUNT(*) OVER () as total_rows
    FROM rides
) AS ranked_rides
WHERE misc_charge > (
    SELECT misc_charge
    FROM (
        SELECT misc_charge,
               ROW_NUMBER() OVER (ORDER BY misc_charge) as rn,
               COUNT(*) OVER () as total_rows
        FROM rides
    ) as inner_ranked_rides
    WHERE rn = FLOOR(0.75 * total_rows) + 1  -- Calculate 75th percentile row number
)
AND ride_status = 'completed';
---------------------------------------------------------------------------------------
-- 19. Detect duplicate ride IDs if any.
SELECT 
	ride_id,
	COUNT(ride_id) AS duplicate_count
FROM rides
GROUP BY ride_id
HAVING COUNT(ride_id) > 1;
--------------------------------------------------------------------------------------------
-- 20. Create a **revenue forecasting table** using historical ride data.










    
    
    
    
    
    
    
    
    
    
    
    
    