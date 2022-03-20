
set -eu
set -o pipefail

check() {
    filepath=$1
    code=$(cat $filepath| (grep '^\$ ' || true) | cut -b3- | head -n1)
    echo -e "\e[34m$filepath\e[0m"
    cat $filepath | (grep '^< ' || true) | cut -b3- > var/input.txt
    cat $filepath | (grep '^> ' || true) | cut -b3- > var/expected.txt
    cat $filepath
    $code | strip_diff > var/actual.txt
    if ! diff -u var/expected.txt var/actual.txt > /dev/null; then
        echo
        cat var/actual.txt | sed -e 's/^/> /g'
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
if [ "$#" = 0 ]; then
    for f in $(ls test/*.txt); do
        check $f || exit 1
    done
else
    while [ "$#" != 0 ]; do
        f=$1
        shift
        check $f || r=1
    done
fi

#HHMM=$(TZ= date +%H%M)

if [ "$r" = 0 ]; then
    echo All OK
else
    echo NG
    exit 1
fi

