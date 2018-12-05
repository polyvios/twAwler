oldest=$1
#echo $@
shift
for link in $@ ; do
  ln -sf $oldest $link
done
