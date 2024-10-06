-- Duración Promedio de las Canciones por Año con 2 decimales  
SELECT release_year, ROUND(AVG(duration), 2) AS avg_duration
FROM track
GROUP BY release_year
ORDER BY release_year;

-- Tempo Promedio de las Canciones por Año con 2 decimales  
SELECT release_year, ROUND(AVG(tempo)) AS avg_tempo
FROM track
GROUP BY release_year
ORDER BY release_year;

-- Duración Promedio de las Canciones por lustro con 2 decimales 
SELECT 
    lustrum,
    ROUND(AVG(duration), 2) AS avg_duration
FROM track
GROUP BY lustrum
ORDER BY lustrum;

-- Tempo Promedio de las Canciones por Lustro con 2 decimales  
SELECT 
	lustrum, 
	ROUND(AVG(tempo)) AS avg_tempo
FROM track
GROUP BY lustrum
ORDER BY lustrum;

-- Popularidad relacionada con energía y danceability 
-- Hay que tener en cuenta que la popularidad es a día de hoy, 
-- asíque claro que las canciones antiguas son menos populares, 
-- además de que no estamos cogiendo en los dos primeros lustros 
-- solamente las más populares sino muchas populares.
SELECT 
    lustrum,
    ROUND(AVG(danceability),2) AS avg_danceability,
    ROUND(AVG(energy),2) AS avg_energy,
    ROUND(AVG(sp_popularity),2) AS avg_popularity
FROM 
    track
GROUP BY 
    lustrum
ORDER BY 
    lustrum;
    
-- Borrar si existe la lista temporal de 25 canciones 
DROP TEMPORARY TABLE IF EXISTS random_titles;
-- Crear la temporary table con el title solo (esto puede estar mejor hecho 
-- para no coger canciones que no tengan weeks en el chart)
CREATE TEMPORARY TABLE random_titles AS
SELECT 
    t.title
FROM 
    track t
WHERE 
    t.weeks is not null
ORDER BY 
	RAND()
LIMIT 25;

-- Aquí sacamos toda esa info, y más si queremos, 
-- si quitas MAX deja de funcionar y no te deja hacer el group by
-- a pesar de ser valores todos iguales
SELECT 
    t.title, 
    MAX(c.name) AS chart_name,  -- Usar MAX() u otra función de agregación
    MAX(t.weeks) AS weeks,
    MAX(t.track_id) AS track_id,
    MAX(t.energy) AS energy,
    MAX(t.danceability) AS danceability,
    MAX(t.valence) AS valence,
    MAX(t.track_mode) AS track_mode,
    MAX(t.track_key) AS track_key
FROM 
    track t
JOIN 
    chart_entry ce ON t.track_id = ce.track_id
JOIN 
    chart_update cu ON ce.update_id = cu.update_id
JOIN 
    chart c ON cu.chart_id = c.chart_id
JOIN 
    random_titles rt ON t.title = rt.title
GROUP BY 
    t.title
ORDER BY 
    t.title;

-- Mirando si los títulos solo llegan hasta la L 
-- porque no sé si el random está funcionando bien

SELECT DISTINCT LEFT(t.title, 1) AS first_letter
FROM track t
JOIN chart_entry ce ON t.track_id = ce.track_id
JOIN chart_update cu ON ce.update_id = cu.update_id
JOIN chart c ON cu.chart_id = c.chart_id
WHERE t.weeks is not null
ORDER BY first_letter;