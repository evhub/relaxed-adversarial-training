from undebt.pattern.util import (
    tokens_as_dict,
    tokens_as_list,
    attach,
)
from undebt.pyparsing import (
    Literal,
    SkipTo,
    OneOrMore,
    Optional,
    originalTextFor,
    nestedExpr,
)
from undebt.pattern.common import (
    NL,
    ANY_CHAR,
    WHITE,
    NUM,
)
from undebt.cmd.logic import (
    create_find_and_replace,
    parse_grammar,
    _transform_results,
)


# util:
NUM = originalTextFor(NUM)

REST_OF_LINE = originalTextFor(NL | (ANY_CHAR | WHITE) + SkipTo(NL) + NL)

@tokens_as_list(assert_len=1)
def trim(tokens):
    return tokens[0][1:-1]

BRACES = attach(originalTextFor(nestedExpr("{", "}", ignoreExpr=NL)), trim)

BRACKETS = attach(originalTextFor(nestedExpr("[", "]", ignoreExpr=NL)), trim)


# setup:
patterns_list = []


# begin document:
begin_document_grammar = Literal("\\begin{document}")

def begin_document_replace(tokens):
    return "TODO: strip LaTeX header material."

patterns_list.append((begin_document_grammar, begin_document_replace))


# end document:
end_document_grammar = Literal("\\end{document}") + NL

def end_document_replace(tokens):
    return ""

patterns_list.append((end_document_grammar, end_document_replace))


# section:
section_grammar = (
    Literal("\\section") + BRACES("name") + NL
    + Optional(Literal("\\label{sec:") + NUM + Literal("}") + NL)
    + Optional(Literal("\\cftchapterprecistoc") + BRACES + NL)
)

@tokens_as_dict(assert_keys=("name",))
def section_replace(tokens):
    return "&nbsp;\n\n## " + tokens["name"] + "\n"

patterns_list.append((section_grammar, section_replace))


# subsection:
subsection_grammar = (
    Literal("\\subsection") + BRACES("name")
)

@tokens_as_dict(assert_keys=("name",))
def subsection_replace(tokens):
    return "**" + tokens["name"] + "**"

patterns_list.append((subsection_grammar, subsection_replace))


# label:
label_grammar = (
    Literal("\\label") + BRACES + WHITE
)

def label_replace(tokens):
    return ""

patterns_list.append((label_grammar, label_replace))


# ital:
ital_grammar = (
    Literal("\\textit") + BRACES("text")
)

@tokens_as_dict(assert_keys=("text",))
def ital_replace(tokens):
    return "_" + tokens["text"] + "_"

patterns_list.append((ital_grammar, ital_replace))


# bf:
bf_grammar = (
    Literal("\\textbf") + BRACES("text")
)

@tokens_as_dict(assert_keys=("text",))
def bf_replace(tokens):
    return "**" + tokens["text"] + "**"

patterns_list.append((bf_grammar, bf_replace))


# footnote:
footnote_grammar = (
    Literal("\\footnote") + BRACES("footnote")
    + REST_OF_LINE("text")
)

global footnotes_seen
footnotes_seen = 0

@tokens_as_dict(assert_keys=("footnote", "text"))
def footnote_replace(tokens):
    global footnotes_seen
    footnotes_seen += 1
    return (
        "[^" + str(footnotes_seen) + "] "
        + tokens["text"] + "\n"
        + "[^" + str(footnotes_seen) + "]: "
        + tokens["footnote"] + "\n\n"
    )

patterns_list.append((footnote_grammar, footnote_replace))


# enumerate:
enumerate_grammar = (
    Literal("\\begin{enumerate}").suppress() + NL.suppress()
    + OneOrMore(Literal("\\item").suppress() + REST_OF_LINE)
    + Literal("\\end{enumerate}").suppress()
)

@tokens_as_list()
def enumerate_replace(tokens):
    out = "\n"
    for i, item in enumerate(tokens):
        out += str(i + 1) + ". " + item
    return out

patterns_list.append((enumerate_grammar, enumerate_replace))


# itemize:
itemize_grammar = (
    Literal("\\begin{itemize}").suppress() + NL.suppress()
    + OneOrMore(Literal("\\item").suppress() + REST_OF_LINE)
    + Literal("\\end{itemize}").suppress()
)

@tokens_as_list()
def itemize_replace(tokens):
    out = ""
    for item in tokens:
        out += "- " + item
    return out

patterns_list.append((itemize_grammar, itemize_replace))


# autoref:
autoref_grammar = (
    Literal("\\autoref") + BRACES("name")
)

@tokens_as_dict(assert_keys=("name",))
def autoref_replace(tokens):
    return "[reference to " + tokens["name"] + "](TODO)"

patterns_list.append((autoref_grammar, autoref_replace))


# href links:
href_grammar = (
    Literal("\\href") + BRACES("link") + BRACES("text")
)

@tokens_as_dict(assert_keys=("link", "text"))
def href_replace(tokens):
    return "[" + tokens["text"] + "](" + tokens["link"] + ")"

patterns_list.append((href_grammar, href_replace))


# dash:
dash_grammar = Literal("---")

def dash_replace(tokens):
    return "—"

patterns_list.append((dash_grammar, dash_replace))


# open quote:
open_quote_grammar = Literal("``")

def open_quote_replace(tokens):
    return "“"

patterns_list.append((open_quote_grammar, open_quote_replace))


# close quote:
close_quote_grammar = Literal("''")

def close_quote_replace(tokens):
    return "”"

patterns_list.append((close_quote_grammar, close_quote_replace))


# newline artifacts:
nl_artifact_grammar = Literal("\n\n\n")

def nl_artifact_replace(tokens):
    return "\n\n"

patterns_list.append((nl_artifact_grammar, nl_artifact_replace))


# math:
math_grammar = (
    Literal("\\[")
    | Literal("\\]")
)

def math_replace(tokens):
    return "$$"

patterns_list.append((math_grammar, math_replace))


# begin align*:
begin_align_grammar = NL + Literal("\\begin{align*}")

def begin_align_replace(tokens):
    return "\n$$\\begin{align*}"

patterns_list.append((begin_align_grammar, begin_align_replace))


# end align*:
end_align_grammar = Literal("\\end{align*}") + NL

def end_align_replace(tokens):
    return "\\end{align*}$$\n"

patterns_list.append((end_align_grammar, end_align_replace))


# argmax:
argmax_grammar = Literal("\\argmax")

def argmax_replace(tokens):
    return "\\text{argmax}"

patterns_list.append((argmax_grammar, argmax_replace))


# argmin:
argmin_grammar = Literal("\\argmin")

def argmin_replace(tokens):
    return "\\text{argmin}"

patterns_list.append((argmin_grammar, argmin_replace))


# comments:
comment_grammar = NL + Literal("%") + REST_OF_LINE("comment")

@tokens_as_dict(assert_keys=("comment",))
def comment_replace(tokens):
    return "\nTODO: " + tokens["comment"]

patterns_list.append((comment_grammar, comment_replace))


# main:
def main(source, target):
    with open(source, "tr", encoding="utf-8") as fp:
        text = fp.read()

        global footnotes_seen
        footnotes_seen += text.count("[^") // 2

        for i, (grammar, replace) in enumerate(patterns_list):
            print("running pattern {}...".format(replace.__name__[:-len("_replace")]))

            # keep running grammar until it stops producing results
            j = 0
            while True:
                print("\tpass {}...".format(j + 1))
                j += 1
                find_and_replace = create_find_and_replace(grammar, replace)
                results = parse_grammar(find_and_replace, text)
                if not results:
                    break
                else:
                    text = _transform_results(results, text)

    with open(target, "tw", encoding="utf-8") as fp:
        fp.seek(0)
        fp.truncate()
        fp.write(text)


if __name__ == "__main__":
    main("./main.tex", "./main.md")
