<?php
  require_once __DIR__ . '/vendor/autoload.php';

  use PhpParser\NodeFinder;
  use PhpParser\NodeTraverser;
  use PhpParser\Node;
  use PhpParser\Node\Expr\FuncCall;
  use PhpParser\Node\Expr\Variable;
  use PhpParser\PrettyPrinter;

  $encoded_ast = fgets(STDIN);              /* Read encoded AST from python STDIN pipe */
  $constructed_funcs = array();

  /********** Init AST Tools **********/
  $fc_detector = new NodeFinder;                                /* Finder to detect FC */
  $fc_replacer = new NodeTraverser;                      /* Traverser to replace names */
  $printer = new PrettyPrinter\Standard;

  try {                                                                      /* Decode */
    $JsonDecoder = new PhpParser\JsonDecoder();
    $ast = $JsonDecoder->decode($encoded_ast);
  } catch (Throwable $e) { return; } 

  if( $ast === null ) { return; }

  /********** Detect Function Construction **********/
  $calls = $fc_detector->find( $ast, 
    function(Node $node) {
      return ($node instanceof FuncCall)
        && ($node->name instanceof Variable);
    }
  );

  foreach($calls as $c) { 
    $var_name = $c->name->name;
    $constructed_funcs[$var_name] = "func_name"; 
    /********** Find Assignment Nodes **********/
    $assignments = $fc_detector->find($ast, 
      function(Node $node) {
        if( ($node instanceof Node\Expr\Assign)
          && ($node->var instanceof Variable) ) {
            global $var_name;
            if(!strcmp((string) $node->var->name, $var_name)) {
              return TRUE;
            } else { return FALSE; }
          } else { return FALSE; }
      }
    );

    /********** Resolve Function Names **********/
    foreach($assignments as $assignment) {
      $function_name = NULL;
      try {
        eval( 
              "\$function_name = " .
              $printer->prettyPrintExpr($assignment->expr) .
              ";"
            );
      } catch (Throwable $e) { /* couldn't resolve function name */ }

      if( $function_name ) {
        $constructed_funcs[$var_name] = $function_name;
      }
    }
  }

  if(count($constructed_funcs) === 0) {
    echo json_encode(array("constructed" => array()));
  } else {
    $code = $printer->prettyPrint($ast);

    foreach(array_keys($constructed_funcs) as $f) {
      $call = '/\$' . $f . '\(/';
      $true_call = $constructed_funcs[$f]. '(';
      $code = preg_replace($call, $true_call, $code);
    }

    $code = "<?php\n" . $code . "\n?>";
    
    $tempfile = "./tmp";
    $rv = file_put_contents($tempfile, $code);

    if(!$rv) { echo "Error dumping to tmp file!\n"; return; }
    
    /********** ProgPilot **********/
    $context = new \progpilot\Context;                            /* progpilot context */
    $analyzer = new \progpilot\Analyzer;                        /* taint analysis pass */

    $context->inputs->setFile($tempfile);                        /* configure analysis */
    $context->setConfiguration("./progpilot_config/config.yml");

    $analyzer->run($context);                                    /* run taint analysis */

    /********** Results **********/
    $results = $context->outputs->getResults();

    echo json_encode(
                      array(
                        "constructed" => array_values($constructed_funcs),
                        "progpilot" => $results
                      )
                    );
  }
?>
