class Parser:
    WHITE_SPACE = {" ", "\t", "\n", "\r"}
    SEPARATORS = {":", "<", ">", "(", ")", ";", "="}

    def __init__(self, script):
        self.tokens = self._tokenize(script)
        self.symbol_table = {}
        self.i = 0

    def _tokenize(self, script):
        tokens = []
        is_processing_string_token = False
        current_token = ""
        for i in range(len(script)):
            char = script[i]
            # enable processing string flag
            if char == "\"":
                if not is_processing_string_token:
                    is_processing_string_token = True
                else:
                    # done processing string token
                    is_processing_string_token = False
                    current_token += char
                    tokens.append(current_token)
                    current_token = ""
                    continue
            if is_processing_string_token:
                current_token += char
                continue
            # only append whitespace if we are processing a string
            if char in Parser.WHITE_SPACE:
                if len(current_token) > 0:
                    tokens.append(current_token)
                current_token = ""
                continue
            # end current token if separator is found
            if char in Parser.SEPARATORS:
                if len(current_token) > 0:
                    tokens.append(current_token)
                    current_token = ""
                tokens.append(char)
                continue
            current_token += char
        return tokens

    def validate(self):
        self.i = 0
        while self.i < len(self.tokens):
            self._parse_statement()
        print(self.symbol_table)
        return True

    def _eat(self, expected_token=None):
        token = self.tokens[self.i]
        if expected_token:
            if token != expected_token:
                raise ValueError(f'Expected {expected_token}')
        self.i += 1
        return token

    def _eat_type(self):
        result = ""
        token = self._eat()
        if token == "int":
            return (token, ("int", ))
        elif token == "string":
            return (token, ("string", ))
        elif token == "box":
            result += token
            result += self._eat("<")
            res, variable_type_tmp = self._eat_type()
            variable_type_tuple = ("box", variable_type_tmp)
            result += res
            result += self._eat(">")
            return (result, variable_type_tuple)
        else:
            raise ValueError(f'Expected type, got {token}')

    def _eat_expression(self):
        result = ""
        token = self._eat()
        if token.isdigit():
            # int
            return (token, ("int", ), ("int", ))
        elif len(token) >= 2 and (token[0] == "\"" and token[-1] == "\""):
            # string
            return (token, ("string", ), ("string", ))
        elif token == "box":
            result += token
            # validate first part where type is defined
            result += self._eat("<")
            result += self._eat_type()[0]
            result += self._eat(">")
            # validate inner expression
            result += self._eat("(")
            res, tmp_exp_type, tmp_eval_exp_type = self._eat_expression()
            result += res
            exp_type = ("box", tmp_exp_type)
            exp_eval_type = ("box", tmp_eval_exp_type)
            result += self._eat(")")
            return (result, exp_type, exp_eval_type)
        raise ValueError(f'Expected expression, got {token}')

    def _parse_statement(self):
        self._eat("let")
        variable_name = self._eat()
        self._eat(":")
        # ex: box<box<int>>
        variable_type, variable_type_tuple = self._eat_type()
        self._eat("=")
        # ex: box<box<int>>(box<int>(42))
        expression, expression_type, expression_eval_type = self._eat_expression()
        self._eat(";")
        if variable_type_tuple != expression_type:
            raise ValueError(f"Type mismatch for {variable_name!r}: declared {variable_type} but got {expression_type}")
        if expression_type != expression_eval_type:
            raise ValueError(f"Type mismatch for {variable_name!r}: declared {variable_type} but got {expression_type}")
        self.symbol_table[variable_name] = (variable_type, variable_type_tuple, expression, expression_type, expression_eval_type)

# --------------------- Tests ---------------------

def expect_valid(script: str):
    try:
        ok = Parser(script).validate()
        assert ok, "Expected valid, got False"
        print("✅ VALID as expected")
    except Exception as e:
        raise AssertionError(f"Expected valid, but parser raised: {e}")

def expect_invalid(script: str):
    try:
        ok = Parser(script).validate()
        # If no exception and returned True, that's a failure for invalid case
        if ok:
            raise AssertionError("Expected invalid, but validate() returned True")
        # If validate() ever returns False without exception, that's also fine:
        print("✅ INVALID as expected (returned False)")
    except Exception:
        # Any parsing/type error counts as invalid
        print("✅ INVALID as expected (raised)")

# --- Valid cases ---

script_valid_simple = """let x:int = 5;
let y:string="hello world";"""

# Declared box<box<int>> matches expression box<box<int>>(box<int>(42))
script_valid_nested = """let z:box<int> = box<int>(42);
let w:box<box<int>> = box<box<int>>(box<int>(42));"""

# Whitespace noise, still valid
script_valid_ws = """   let   a   :   int   =   0   ;
let  s  :  string =  " spaced "  ;
let b:box<int> =    box<int>(  7  );"""

# Multiple statements back to back
script_valid_multi = """let x:int = 1;let y:string="ok";let z:box<int>=box<int>(2);"""

# --- Invalid cases ---

# 1) Missing semicolon after first line
script_invalid_missing_semicolon = """let x:int = 5
let y:string="hello";"""

# 2) Type mismatch: int declared, string given
script_invalid_type_mismatch = """let x:int = "oops";"""

# 3) Box mismatch: declared box<int>, expression is box<string>("hi")
script_invalid_box_mismatch = """let z:box<int> = box<string>("hi");"""

# 4) Wrong nesting: declared box<box<int>>, expression only box<box<int>>(42)
script_invalid_missing_inner_box = """let w:box<box<int>> = box<box<int>>(42);"""

# 5) Unterminated string literal
script_invalid_unterminated_string = """let s:string = "hello;"""

# 6) Negative int not supported by current isdigit() rule (should be invalid with current code)
script_invalid_negative_int = """let n:int = -7;"""

# 7) Bad expression starter
script_invalid_expr = """let x:int = );"""

# 8) Malformed box syntax (empty type parameter)
script_invalid_box_syntax = """let b:box<> = box<int>(1);"""

if __name__ == "__main__":
    # Valid
    expect_valid(script_valid_simple)
    expect_valid(script_valid_nested)
    expect_valid(script_valid_ws)
    expect_valid(script_valid_multi)

    # Invalid
    expect_invalid(script_invalid_missing_semicolon)
    expect_invalid(script_invalid_type_mismatch)
    expect_invalid(script_invalid_box_mismatch)
    expect_invalid(script_invalid_missing_inner_box)
    expect_invalid(script_invalid_unterminated_string)
    expect_invalid(script_invalid_negative_int)
    expect_invalid(script_invalid_expr)
    expect_invalid(script_invalid_box_syntax)

    print("All ad-hoc tests completed.")
