SELECT
  pct_id,
  month,
  SUM(numerator) AS numerator,
  SUM(denominator) AS denominator,
  IEEE_DIVIDE(SUM(numerator), SUM(denominator)) AS calc_value
  {denominator_aliases}
  {numerator_aliases}
FROM
  {from_table}
JOIN ebmdatalab.hscic.ccgs AS ccgs
ON (ccgs.code = pct_id AND ccgs.org_type = 'CCG')
GROUP BY
  pct_id,
  month
ORDER BY
  month
