function cfmt --description "clang-format every C and C++ source file under the current folder"
    find . -type f \( -name '*.c' -o -name '*.h' -o -name '*.cc' -o -name '*.hh' -o -name '*.cpp' -o -name '*.hpp' \) -not -path './.git/*' -print0 | xargs -0 -r clang-format -i
end

function easypush --description "easypush MESSAGE FILE...: make clean, format C/C++, commit FILEs, push"
    if test (count $argv) -lt 2; or test "$argv[1]" = -h
        echo "usage: easypush MESSAGE FILE..."
        return 1
    end
    if test -f Makefile; or test -f makefile
        make clean; or return
    end
    cfmt; or return
    git add -- $argv[2..-1]; or return
    git commit -m "$argv[1]"; or return
    git push
end

function gtag --description "gtag TAG: create TAG and push it; the local tag is removed if the push fails"
    if test (count $argv) -ne 1
        echo "usage: gtag TAG"
        return 1
    end
    git tag -- $argv[1]; or return
    if not git push origin -- $argv[1]
        git tag -d -- $argv[1]
        return 1
    end
end
