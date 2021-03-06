{# ===== Fetch list of Database object types(View) ===== #}
{% if node_id %}
SELECT
    c.relname AS name,
    'View' AS object_type,
    'icon-view' AS icon,
    '{{ nspname }}' AS nspname
FROM
    pg_class c
LEFT OUTER JOIN pg_tablespace spc ON spc.oid=c.reltablespace
LEFT OUTER JOIN pg_description des ON (des.objoid=c.oid and des.objsubid=0 AND des.classoid='pg_class'::regclass)
LEFT OUTER JOIN pg_class tst ON tst.oid = c.reltoastrelid
WHERE
    ((c.relhasrules AND (EXISTS (
      SELECT
          r.rulename
      FROM
          pg_rewrite r
      WHERE
          ((r.ev_class = c.oid)
          AND (bpchar(r.ev_type) = '1'::bpchar))
      ))
     ) OR (c.relkind = 'v'::char)
    )
    AND c.relnamespace = {{ node_id }}::oid
ORDER BY
    c.relname
{% endif %}
