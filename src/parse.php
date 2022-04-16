<?php

const variableRegex = "/(LF|TF|GF)@[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*/";
const integerRegex = "/int@-?[0-9]*/";
const identificatorRegex = "/[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*/";

const types = array("int", "string", "bool");

function checkEscapes($string)
{
  $input_length = strlen($string);
  
  for ($x = 0; $x < $input_length; $x++)
  {
    if ($string[$x] == '\\')
    {
      if (($input_length - $x - 1) >= 3 && is_numeric($string[$x + 1]) && is_numeric($string[$x + 2]) && is_numeric($string[$x + 3]))
      {
        $val = intval(substr($string, $x + 1, 4));

        // Exclude invalid characters
        if (($val >= 0 && $val <= 32) || ($val >= 35 && $val <= 92))
        {                   
          $x += 4;
          continue;
        }
        else 
          return false;
      }
      else
        return false;
    }
  }

  return true;
}

function variableRegex($string)
{
  return preg_match(variableRegex, $string);
}

function integerRegex($string)
{
  return preg_match(integerRegex, $string);
}

function isBool($string)
{
  if ($string == "bool@true" || $string == "bool@false") return true;
  return false;
}

function isNil($string) 
{
  return "nil@nil" == $string;
}

function symbolRegex($string) 
{
  return (variableRegex($string) || integerRegex($string) || isBool($string) || (preg_match("/string@*/", $string) && checkEscapes(substr($string, 7))) || isNil($string));
}

function identificatorRegex($string)
{
  return preg_match(identificatorRegex, $string);
}

function isType($string)
{
  foreach (types as $type)
  {
    if ($string == $type)
      return true;
  }
  return false;
}

function convertSpecChar($string)
{
  $result = $string;
  $result = str_replace("<", "&lt;", $result);
  $result = str_replace(">", "&gt;", $result);
  return $result;
}

class Argument 
{
  private $type = "";
  private $value = "";

  public function setType($type) 
  {
    $this->type = $type;
  }

  public function setValue($value)
  {
    $this->value = $value;
  }

  public function printXML($argIdx)
  {
      echo("        <arg$argIdx type=\"$this->type\">$this->value</arg$argIdx>\n");
  }
}


class Instruction 
{
  static $instructCount = 0;

  private $name = "";
  private $argField = [];
  
  function incrementCount()
  {
    self::$instructCount++;
  }

  public function setName($newName)
  {
    $this->name = $newName;
    $this->incrementCount();
  }

  public function addArgument($type, $text)
  {
    $newArg = new Argument();
    $newArg->setType($type);
    $argText = $text;

    if ($type == "string")
      $argText = convertSpecChar($argText);

    // If its symbol but not variable then try to remove redundant type
    if (symbolRegex($argText) && !variableRegex($argText))
      $newArg->setValue(substr($argText, strpos($argText, "@") + 1));
    else
      $newArg->setValue($argText);

    array_push($this->argField, $newArg);
  }

  public function printXML() 
  {
    printf("    <instruction order=\"%d\" opcode=\"%s\">\n", self::$instructCount, $this->name);

    foreach ($this->argField as $argIdx=>$value)
      $value->printXML($argIdx + 1);

    echo("    </instruction>\n");
  }

}

function getArgumentDesciptor($string)
{
  if (variableRegex($string))
    return "var";
  elseif (integerRegex($string))
    return "int";
  elseif (isBool($string))
    return "bool";
  elseif (preg_match("/string@*/", $string))
    return "string";
  elseif (isNil($string))
    return "nil";
}

function sanitizeLine($line)
{
  // Remove newline character from end of line
  $line = str_replace(array("\n", "\r"), "", $line);

  // Extract data before comment
  if (($line != "") && (($beforeComment = substr($line, 0, strpos($line, "#"))) || ($line[0] == "#")))
    $line = $beforeComment;
  
  // Remove spaces from start and end of line
  $line = preg_replace("/( |\t)*( $|\t$)/", "", $line);
  $line = preg_replace("/(^ |^\t)( |\t)*/", "", $line);

  return $line;
}

function opError()
{
  error_log("[ERROR] Invalid or unknown operation");
  exit(22);
}

function syntaxError()
{
  error_log("[ERROR] Syntax error");
  exit(23);
}

ini_set('display_errors', 'stderr');
if ($argc > 1)
{
  if ($argc > 2) 
  {
    error_log("[ERROR] Invalid number of arguments");
    exit(10);
  }

  if (($argv[1] == "--help") || ($argv[1] == "-h")) 
  {
    echo("Parser for language IPPcode22

Arguments:
    • -h || --help  to print help

Return codes:
    • 21 - missing IPPcode22 header
    • 22 - unknown operation code
    • 23 - other syntactic error\n");
    exit(0);
  }
}

$headerPresent = false;
while (true)
{
  if (($line = fgets(STDIN)) == false)
    break;

  if (preg_match("~^\s*#~", $line) || preg_match("~^\s*$~", $line))
    continue;

  $line = sanitizeLine($line);

  if ($headerPresent == false)
  {
    if ($line != "")
    {
      if ($line == ".IPPcode22")
      {
        $headerPresent = true;

        echo("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
        echo("<program language=\"IPPcode22\">\n");
      }
      else
      {
        error_log("[ERROR] Missing or invalid header");
        exit(21);
      }
    }
  }
  else 
  {
    $line = preg_replace("/( |\t)+/", " ", $line);
    $lineArray = explode(" ", $line);

    if (sizeof($lineArray) == 0) continue;

    $instruction = strtoupper($lineArray[0]);
    $instructionObject = new Instruction();

    $numbe_of_args = sizeof($lineArray) - 1;

    switch($instruction)
    {
      case "CREATEFRAME":
      case "PUSHFRAME":
      case "POPFRAME":
      case "RETURN":
      case "BREAK":
        if ($numbe_of_args != 0) syntaxError();
        $instructionObject->setName($instruction);
        $instructionObject->printXML();
        break;

      case "DEFVAR":
      case "POPS":
        if ($numbe_of_args != 1) syntaxError();
        if (!variableRegex($lineArray[1])) syntaxError();

        $instructionObject->setName($instruction);
        $instructionObject->addArgument("var", $lineArray[1]);
        $instructionObject->printXML();
        break;

      case "CALL":
      case "LABEL":
      case "JUMP":
        if ($numbe_of_args != 1) syntaxError();
        if (!identificatorRegex($lineArray[1])) syntaxError();

        $instructionObject->setName($instruction);
        $instructionObject->addArgument("label", $lineArray[1]);
        $instructionObject->printXML();
        break;

      case "PUSHS":
      case "WRITE":
        if ($numbe_of_args != 1) syntaxError();
        if (!symbolRegex($lineArray[1])) syntaxError();

        $instructionObject->setName($instruction);
        $instructionObject->addArgument(getArgumentDesciptor($lineArray[1]), $lineArray[1]);
        $instructionObject->printXML();
        break;

      case "MOVE":
      case "INT2CHAR":
      case "STRLEN":
      case "TYPE":
        if ($numbe_of_args != 2) syntaxError();
        if (!variableRegex($lineArray[1]) || !symbolRegex($lineArray[2])) syntaxError();

        $instructionObject->setName($instruction);
        $instructionObject->addArgument("var", $lineArray[1]);
        $instructionObject->addArgument(getArgumentDesciptor($lineArray[2]), $lineArray[2]);
        $instructionObject->printXML();
        break;
              
      case "READ":
        if ($numbe_of_args != 2) syntaxError();
        if (!variableRegex($lineArray[1]) || !isType($lineArray[2])) syntaxError();

        $instructionObject->setName($instruction);
        $instructionObject->addArgument("var", $lineArray[1]);
        $instructionObject->addArgument("type", $lineArray[2]);
        $instructionObject->printXML();
        break;

      case "NOT":
        if ($numbe_of_args != 2) syntaxError();
        if (!variableRegex($lineArray[1]) || !symbolRegex($lineArray[2])) syntaxError();

        $instructionObject->setName($instruction);
        $instructionObject->addArgument("var", $lineArray[1]);
        $instructionObject->addArgument(getArgumentDesciptor($lineArray[2]), $lineArray[2]);
        $instructionObject->printXML();
        break;

      case "ADD":
      case "SUB":
      case "MUL":
      case "IDIV":
      case "LT":
      case "GT":
      case "EQ":
      case "AND":
      case "OR":
      case "STRI2INT":
      case "CONCAT":
      case "GETCHAR":
      case "SETCHAR":
        if ($numbe_of_args != 3) syntaxError();
        if (!variableRegex($lineArray[1]) || !symbolRegex($lineArray[2]) || !symbolRegex($lineArray[3])) syntaxError();

        $instructionObject->setName($instruction);
        $instructionObject->addArgument("var", $lineArray[1]);
        $instructionObject->addArgument(getArgumentDesciptor($lineArray[2]), $lineArray[2]);
        $instructionObject->addArgument(getArgumentDesciptor($lineArray[3]), $lineArray[3]);
        $instructionObject->printXML();
        break;
              
      case "JUMPIFEQ":
      case "JUMPIFNEQ":
        if ($numbe_of_args != 3) syntaxError();
        if (!identificatorRegex($lineArray[1]) || !symbolRegex($lineArray[2]) || !symbolRegex($lineArray[3])) syntaxError();
        
        $instructionObject->setName($instruction);
        $instructionObject->addArgument("label", $lineArray[1]);
        $instructionObject->addArgument(getArgumentDesciptor($lineArray[2]), $lineArray[2]);
        $instructionObject->addArgument(getArgumentDesciptor($lineArray[3]), $lineArray[3]);
        $instructionObject->printXML();
        break;

      default:
        opError();
        break;
    }
  }
}

if ($headerPresent == false)
{
  error_log("[ERROR] Missing or invalid header");
  exit(21);
}

echo("</program>");
?>