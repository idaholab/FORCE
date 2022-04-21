
for a in Regulated Deregulated
do
  for b in CarbonTax Nominal RPS
  do
    for c in Default LNHR
    do
      echo "retrieving ${a}/IL_${b}_${c}/Baseline/baseline.csv"
      cp ${a}/IL_${b}_${c}/Baseline/baseline.csv /projects/hybrid-ies/results/${a:0:1}_${b}_${c}_baseline.csv
    done
  done
done
