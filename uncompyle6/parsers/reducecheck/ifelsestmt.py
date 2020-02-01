#  Copyright (c) 2020 Rocky Bernstein

from uncompyle6.scanners.tok import Token


def ifelsestmt(self, lhs, n, rule, ast, tokens, first, last):
    if (last + 1) < n and tokens[last + 1] == "COME_FROM_LOOP":
        # ifelsestmt jumped outside of loop. No good.
        return True

    if rule not in (
        (
            "ifelsestmt",
            (
                "testexpr",
                "c_stmts_opt",
                "jump_forward_else",
                "else_suite",
                "_come_froms",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "c_stmts_opt",
                "jump_forward_else",
                "else_suite",
                "\\e__come_froms",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "c_stmts_opt",
                "jf_cfs",
                "else_suite",
                "\\e_opt_come_from_except",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "c_stmts_opt",
                "JUMP_FORWARD",
                "else_suite",
                "come_froms",
            ),
        ),
        (
            "ifelsestmt",
            ("testexpr", "c_stmts", "come_froms", "else_suite", "come_froms",),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "c_stmts_opt",
                "jf_cfs",
                "else_suite",
                "opt_come_from_except",
            ),
        ),
        (
            "ifelsestmt",
            (
                "testexpr",
                "c_stmts_opt",
                "jf_cf_pop",
                "else_suite",
            ),
        ),
    ):
        return False
    # Make sure all of the "come froms" offset at the
    # end of the "if" come from somewhere inside the "if".
    # Since the come_froms are ordered so that lowest
    # offset COME_FROM is last, it is sufficient to test
    # just the last one.
    come_froms = ast[-1]
    if come_froms.kind != "else_suite" and self.version >= 3.0:
        if come_froms == "opt_come_from_except" and len(come_froms) > 0:
            come_froms = come_froms[0]
        if not isinstance(come_froms, Token):
            if len(come_froms):
                return tokens[first].offset > come_froms[-1].attr
        elif tokens[first].offset > come_froms.attr:
            return True

    # FIXME: There is weirdness in the grammar we need to work around.
    # we need to clean up the grammar.
    if self.version < 3.0:
        last_token = ast[-1]
    else:
        last_token = tokens[last]
    if last_token == "COME_FROM" and tokens[first].offset > last_token.attr:
        if self.version < 3.0 and self.insts[self.offset2inst_index[last_token.attr]].opname != "SETUP_LOOP":
            return True

    testexpr = ast[0]

    # Check that the condition portion of the "if"
    # jumps to the "else" part.
    if testexpr[0] in ("testtrue", "testfalse"):
        test = testexpr[0]

        else_suite = ast[3]
        assert else_suite == "else_suite"

        if len(test) > 1 and test[1].kind.startswith("jmp_"):
            if last == n:
                last -= 1
            jmp = test[1]
            if self.version > 2.6:
                jmp_target = jmp[0].attr
            else:
                jmp_target = int(jmp[0].pattr)


            # Make sure we don't jump at the end of the "then" inside the "else"
            # (jf_cf_pop may be a 2.6ish specific thing.)
            jump_forward = ast[2]
            if jump_forward == "jf_cf_pop":
                jump_forward = jump_forward[0]

            if jump_forward == "JUMP_FORWARD":
                endif_target = int(jump_forward.pattr)
                last_offset = tokens[last].off2int()
                if endif_target != last_offset:
                    return True

            # The jump inside "else" check below should be added.
            # add this until we can find out what's wrong with
            # not being able to parse:
            #     if a and b or c:
            #         x = 1
            #     else:
            #         x = 2

            # FIXME: add this
            # if jmp_target < else_suite.first_child().off2int():
            #     return True

            if tokens[first].off2int() > jmp_target:
                return True

            return (jmp_target > tokens[last].off2int()) and tokens[
                last
            ] != "JUMP_FORWARD"

    return False
