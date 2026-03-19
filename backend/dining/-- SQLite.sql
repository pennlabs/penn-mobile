-- SQLite
SELECT DISTINCT
  v.venue_id,
  v.name            AS venue_name,
  m.id              AS menu_id,
  m.date            AS menu_date,
  m.service,
  s.id              AS station_id,
  s.name            AS station_name,
--  i.item_id,
  i.name            AS item_name
FROM dining_venue v
JOIN dining_diningmenu m
  ON m.venue_id = v.venue_id
JOIN dining_diningstation s
  ON s.menu_id = m.id
JOIN dining_diningstation_items si
  ON si.diningstation_id = s.id
JOIN dining_diningitem i
  ON i.item_id = si.diningitem_id
WHERE v.venue_id IN (593, 636, 637, 1442)
  AND m.date = '2026-03-25'
  AND station_name = 'comfort'
  AND venue_name = 'English House' 
  -- Hill House, English House, Lauder College House, 1920 Commons
ORDER BY v.name, m.service, s.name, i.name;
