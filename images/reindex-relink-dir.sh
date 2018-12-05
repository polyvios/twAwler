#!/bin/sh

for dir in `echo $@| tr "/" " "`; do
  echo $dir
  find ${dir} -type f | sort | xargs -n 1000 findimagedupes -t '100%' -a --db ${dir}.db --prune | while read line; do echo $line; echo $line | tr " " "\n" | sort | xargs ./replacelink.sh ; done
  find $dir -type l | sort | xargs python ingestdupes.py
  findimagedupes --prune --db ${dir}.db -t '100%'
  #find ${dir} -type f | xargs -n 30 findimagedupes --prune --db ${dir}.db -t '100%' | while read line; do echo $line; echo $line | tr " " "\n" | sort | xargs ./replacelink.sh ; done
  #find $dir -type l | sort | xargs python ingestdupes.py
  findimagedupes --prune --db ${dir}.db -t '100%' -a $dir/ | while read line; do echo $line; echo $line | tr " " "\n" | sort | xargs ./replacelink.sh ; done
  find $dir -type l | sort | xargs python ingestdupes.py
done

rm all.db
#echo Running: findimagedupes -t '100%' --merge=all.db `ls ?.db| xargs -n 1 echo "-f "`
cp 0.db old.db
for d in `ls ?.db`; do
  echo findimagedupes -t "100%" --prune --merge=all.db -f $d -f old.db
  findimagedupes -t "100%" --prune --merge=all.db -f $d -f old.db | while read line; do echo "> $line"; echo $line | tr " " "\n" | sort | xargs ./replacelink.sh ; done
  find $@ -type l | sort | xargs python ingestdupes.py
  mv all.db old.db
done
#findimagedupes -t '100%' --merge=all.db `ls ?.db| xargs -n 1 echo "-f "` | while read line; do echo "> $line"; echo $line | tr " " "\n" | sort | xargs ./replacelink.sh ; done

find $@ -type l | sort | xargs python ingestdupes.py
