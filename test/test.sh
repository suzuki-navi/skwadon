
set -eu
set -o pipefail

basedir=$(dirname $0)/..

targets=()
while [ "$#" != 0 ]; do
    targets+=("$1")
    shift
done
if [ "${#targets[@]}" = 0 ]; then
    cd $(dirname $0)
    targets=(testcloud aws)
    basedir=..
fi

check() {
    filepath=$1
    code=$(cat $filepath| (grep '^\$ ' || true) | cut -b3- | head -n1)
    echo -e "\e[34m$filepath\e[0m"
    cat $filepath | (grep '^< ' || true) | cut -b3- > $basedir/var/input.txt
    cat $filepath | (grep '^> ' || true) | cut -b3- > $basedir/var/expected.txt
    cat $filepath
    (cd $basedir; $code) | strip_diff > $basedir/var/actual.txt
    if ! diff -u $basedir/var/expected.txt $basedir/var/actual.txt > /dev/null; then
        echo
        cat $basedir/var/actual.txt | sed -e 's/^/> /g'
        echo -e "\e[31mNG\e[0m"
        echo "see: diff var/actual.txt var/expected.txt"
        echo
        return 1
    fi
    echo -e "\e[32mOK\e[0m"
    echo
}

strip_diff() {
  cat | (grep -v -E -e '^--- /tmp/' || true) | (grep -v -E -e '^\+\+\+ /tmp/' || true)
}

r=0
for dir in ${targets[@]}; do
    for f in $(find $dir -type f -name '*.txt' | sort); do
        check $f || exit 1
    done
done

#HHMM=$(TZ= date +%H%M)

if [ "$r" = 0 ]; then
    echo -e "\e[32mAll OK\e[0m"
else
    echo -e "\e[31mNG\e[0m"
    exit 1
fi

