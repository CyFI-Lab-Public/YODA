<?php
  require_once __DIR__ . '/vendor/autoload.php';

  use PhpParser\ParserFactory;
  use PhpParser\Error;

  $parser = (new ParserFactory)->create(ParserFactory::PREFER_PHP7);
  $code = file_get_contents($argv[1]);                                    /* Read Code */
  
  $ast = "";
  try                                                             /* Get AST from code */
    { $ast = $parser->parse($code); }
  catch (Error $e) { /* File can't be parsed, invalid PHP? */ }
  
  //print_r($ast);
  echo json_encode($ast);                                              /* return AST */
?>
