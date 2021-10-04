#!/bin/sh

# SET UP ALL DEPENDENCIES FOR PHP-AST

git clone https://github.com/nikic/php-ast

cd php-ast 

phpize
./configure
make
sudo make install

cd .. # BACK TO WD

cp ./php-ast/util.php ./util.php
echo "extension=ast.so" >> php.ini
