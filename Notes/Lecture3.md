# Algorithmic Design

another Level of Computaiton to just comp design
--> Basically writing the function itself
Describe a procedure that builds evrything

## rule based desgin

A → B: A defined element or state is transformed into another.
A + condition → B: A rule applies only when its condition is met.
Repeat the rules → complex result: Simple rules are applied step by step to create more complex outcomes.

## growth based

dendrite and recursive growth

Meine Rules
Also ich möchte hyperbolic surface machen genau dafür brauche ich auch die verwvielfältigung, aber zuerst einen string an dem ich mich abhangel damit sich keine rösschen bilden. Daran vervielfältige ich einseitig

Ich will das sich am anfang eine offene spirale bildet, diese sich aber am ende zu einer koralle also ende an ende wieder schlißt wie eine qualle mit kopf

def: alternating_pseudosphere=alt_ps
also zuerst dann brauch ich einen strand an em ich immer jede schlaufe 2x mache für 3 rotaions und dann abwechselnd 2 rotations mit x3 jede schlaife mache so eregibt sich eine alternierend espriale die einmale weniger abstand vonaniender und einmal mehr hat. es gibt erstmal kein ennde. als parameter nutze ich anzahl wie oft sie sich mit der anzahl der vervielfältigunf drehen soll und die anzahl der vervielfäktigung. dabei bleibt der strand mittig und der seam ist rotierenden ummd en stran ddamit sich eine gleichmäßige abwärtsspirale ergibt

def: hyperbolic_coral=hyp_cor
am ennde, nach einer anzhal roationen n schließt sich der kreis also umfang u des kreises abgewickelt verbindet sich mit start s was an ende von alt_ps anfängt und endet. dieser schlaifenincrease ist ebenfalls parametrisch.

diese def wird ebenfalls genutzt um die corals an irgendwelchen punkten der spirale zu generieren somit an jede n-te windung von alt_ps eine hyp_cor angesetzt. somit wie eine art spirale an der die kugeln sietzen und am ende eine kugel welche runden x 2 hat um doppelt dso goß zu sein dabei ist die koralle in sich geschlossen alt_ps start bleibt offen also ein strand bei alt_ps und ein kreis der x n windungen wächst

branch start von alt_ps ist p (0,0,0) branch start von hyp_cor ist start n-te windung und ende=start
sowie ende alt_ps hyp_coral_end

Parameter hyp_cor:
rounds per alternation also distance between alternations
increasment per alternation per ring alternation a and b: a example: 3 rounds 2x multiplication
length strand start an end

ausgaben: coordinates end strand coordinates ends per round

Parameter hyp_coral:
increase
base chain stitch count --> also the lenghts which defines the circumfurance of the base circle which the first riund stitch count applies to
first round stitch count
rounds (for hyp_coral_end rounds x 2)

Max 3000 stitches#

## GRID
