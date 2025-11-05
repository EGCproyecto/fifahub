import re
import itertools
from typing import Optional

from flamapy.core.models.ast import ASTOperation
from flamapy.core.transformations import ModelToModel
from flamapy.metamodels.fm_metamodel.models import FeatureModel, Feature, Relation, Constraint
from flamapy.metamodels.bdd_metamodel.models import BDDModel


class FmToBDD(ModelToModel):

    @staticmethod
    def get_source_extension() -> str:
        return "fm"

    @staticmethod
    def get_destination_extension() -> str:
        return "bdd"

    def __init__(self, source_model: FeatureModel) -> None:
        self.source_model = source_model
        self.destination_model: Optional[BDDModel] = None
        self._counter: int = 0

    def transform(self) -> BDDModel:
        self.destination_model = BDDModel()
        for feature in self.source_model.get_features():
            self._add_feature(feature)
        formula = self._traverse_feature_tree()
        self.destination_model.build_bdd(formula)
        return self.destination_model

    def _add_feature(self, feature: Feature) -> str:
        assert self.destination_model is not None, "destination_model is None"
        if feature.name not in self.destination_model.features_variables:
            variable = secure_variable_name(feature.name, self._counter)
            self.destination_model.variables_features[variable] = feature.name
            self.destination_model.features_variables[feature.name] = variable
            self._counter += 1
        return self.destination_model.features_variables[feature.name]

    def _traverse_feature_tree(self) -> str:
        """Traverse the feature tree from the root and return the propositional formula."""
        if self.source_model is None or self.source_model.root is None:
            return ''
        assert self.destination_model is not None, "destination_model is None"
        # The root is always present
        root_feature = self.source_model.root
        formula = [self.destination_model.features_variables[root_feature.name]]  
        for feature in self.source_model.get_features():
            for relation in feature.get_relations():
                formula.append(self._get_relation_formula(relation))
        for constraint in self.source_model.get_constraints():
            formula.append(self._get_constraint_formula(constraint))
        propositional_formula = ' & '.join(f'({f})' for f in formula)
        return propositional_formula

    def _get_relation_formula(self, relation: Relation) -> str:
        result = ''
        if relation.is_mandatory():
            result = self._get_mandatory_formula(relation)
        elif relation.is_optional():
            result = self._get_optional_formula(relation)
        elif relation.is_or():
            result = self._get_or_formula(relation)
        elif relation.is_alternative():
            result = self._get_alternative_formula(relation)
        elif relation.is_mutex():
            result = self._get_mutex_formula(relation)
        elif relation.is_cardinal():
            result = self._get_cardinality_formula(relation)
        return result

    def _get_mandatory_formula(self, relation: Relation) -> str:
        assert self.destination_model is not None, "destination_model is None"
        parent = self.destination_model.features_variables[relation.parent.name]
        child = self.destination_model.features_variables[relation.children[0].name]
        return f'{parent} <=> {child}'

    def _get_optional_formula(self, relation: Relation) -> str:
        assert self.destination_model is not None, "destination_model is None"
        parent = self.destination_model.features_variables[relation.parent.name]
        child = self.destination_model.features_variables[relation.children[0].name]
        return f'{child} => {parent}'

    def _get_or_formula(self, relation: Relation) -> str:
        assert self.destination_model is not None, "destination_model is None"
        parent = self.destination_model.features_variables[relation.parent.name]
        children = " | ".join(
            self.destination_model.features_variables[child.name] 
            for child in relation.children
        )
        return f'{parent} <=> ({children})'

    def _get_alternative_formula(self, relation: Relation) -> str:
        formula = []
        assert self.destination_model is not None, "destination_model is None"
        parent = self.destination_model.features_variables[relation.parent.name]
        children = [self.destination_model.features_variables[child.name] 
                    for child in relation.children]
        for child in children:
            children_negatives = set(children) - {child}
            formula.append(f'{child} <=> '
                           f'({" & ".join("!" + ch for ch in children_negatives)} '
                           f'& {parent})')
        return " & ".join(f'({f})' for f in formula)

    def _get_mutex_formula(self, relation: Relation) -> str:
        formula = []
        assert self.destination_model is not None, "destination_model is None"
        parent = self.destination_model.features_variables[relation.parent.name]
        children = {self.destination_model.features_variables[child.name] 
                    for child in relation.children}
        for child in children:
            children_negatives = children - {child}
            formula.append(f'{child} <=> '
                           f'({" & ".join("!" + cn for cn in children_negatives)} '
                           f'& {parent})')
        formula_str = " & ".join(f'({f})' for f in formula)
        return f'({parent} <=> ' \
            f'!({" | ".join(child for child in children)})) | ({formula_str})'

    def _get_cardinality_formula(self, relation: Relation) -> str:
        assert self.destination_model is not None, "destination_model is None"
        parent = self.destination_model.features_variables[relation.parent.name]
        children = {self.destination_model.features_variables[child.name] 
                    for child in relation.children}
        or_ctc = []
        for k in range(relation.card_min, relation.card_max + 1):
            combi_k = list(itertools.combinations(children, k))
            for positives in combi_k:
                negatives = children - set(positives)
                positives_and_ctc = f'{" & ".join(positives)}'
                negatives_and_ctc = f'{" & ".join("!" + f for f in negatives)}'
                if positives_and_ctc and negatives_and_ctc:
                    and_ctc = f'{positives_and_ctc} & {negatives_and_ctc}'
                else:
                    and_ctc = f'{positives_and_ctc}{negatives_and_ctc}'
                or_ctc.append(and_ctc) 
        formula_or_ctc = f'{" | ".join(or_ctc)}'
        return f'{parent} <=> {formula_or_ctc}'

    def _get_constraint_formula(self, ctc: Constraint) -> str:
        assert self.destination_model is not None, "destination_model is None"
        constraint_str = secure_constraint(ctc, self.destination_model.features_variables)
        constraint_str = re.sub(rf"\b{ASTOperation.XOR.value}\b", 
                                BDDModel.LogicConnective.XOR.value, constraint_str)
        constraint_str = re.sub(rf"\b{ASTOperation.NOT.value}\b", 
                                BDDModel.LogicConnective.NOT.value, constraint_str)
        constraint_str = re.sub(rf"\b{ASTOperation.AND.value}\b", 
                                BDDModel.LogicConnective.AND.value, constraint_str)
        constraint_str = re.sub(rf"\b{ASTOperation.OR.value}\b", 
                                BDDModel.LogicConnective.OR.value, constraint_str)
        constraint_str = re.sub(rf"\b{ASTOperation.IMPLIES.value}\b", 
                                BDDModel.LogicConnective.IMPLIES.value, constraint_str)
        constraint_str = re.sub(rf"\b{ASTOperation.EQUIVALENCE.value}\b", 
                                BDDModel.LogicConnective.EQUIVALENCE.value, constraint_str)
        constraint_str = re.sub(rf"\b{ASTOperation.REQUIRES.value}\b", 
                                BDDModel.LogicConnective.IMPLIES.value, constraint_str)
        constraint_str = re.sub(
            rf"\b{ASTOperation.EXCLUDES.value}\b",
            f'{BDDModel.LogicConnective.IMPLIES.value} {BDDModel.LogicConnective.NOT.value}',
            constraint_str
        )
        return constraint_str


def secure_variable_name(name: str, counter: int) -> str:
    allowed_characters = re.findall(r'[a-zA-Z0-9_]', name)
    if not allowed_characters:
        return f'n{counter}'
    if allowed_characters[0].isdigit():  # Ensure the first character is not a digit
        allowed_characters = [char for char in allowed_characters if not char.isdigit()]
    return f'n{counter}_{"".join(allowed_characters)}'


def secure_constraint(ctc: Constraint, features_variables: dict[str, str]) -> str:
    formula = ctc.ast.pretty_str()
    for feature in ctc.get_features():
        formula = substitute_quoted_word(formula, f'"{feature}"', features_variables[feature])
        formula = re.sub(rf"\b{feature}\b", features_variables[feature], formula)
    return formula


def substitute_quoted_word(text: str, quoted_word: str, replacement_word: str) -> str:
    # Ensure the quoted_word has double quotes around it
    if not (quoted_word.startswith('"') and quoted_word.endswith('"')):
        raise ValueError("The quoted_word parameter must be surrounded by double quotes.")
    # Remove the double quotes for regex matching
    word_to_replace = quoted_word.strip('"')
    # Create a regex pattern to find the quoted word in the text
    pattern = rf'"{re.escape(word_to_replace)}"'
    # Replace the quoted word with the replacement word
    return re.sub(pattern, replacement_word, text)
