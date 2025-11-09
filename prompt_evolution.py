#!/usr/bin/env python3
"""
Auto-Evolving Prompts: Evolutionary Prompt Optimization

Prompts that evolve and improve themselves through genetic algorithms,
achieving superhuman prompt engineering through natural selection.
"""

import json
import random
import asyncio
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re
import statistics

try:
    from .agent_system import BaseAgent
except ImportError:
    from agent_system import BaseAgent


class MutationType(Enum):
    """Types of prompt mutations."""
    REPHRASE = "rephrase"
    CONTEXT_MODIFY = "context_modify"
    FORMALITY_ADJUST = "formality_adjust"
    RESTRUCTURE = "restructure"
    EXAMPLE_FORMAT = "example_format"
    DIRECTIVE_STRENGTH = "directive_strength"
    CONSTRAINT_MODIFY = "constraint_modify"
    SPECIFICITY_ADJUST = "specificity_adjust"
    CROSS_POLLINATE = "cross_pollinate"
    CREATIVE_RANDOM = "creative_random"


class FitnessDimension(Enum):
    """Dimensions for evaluating prompt fitness."""
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    EFFICIENCY = "efficiency"
    ROBUSTNESS = "robustness"
    CLARITY = "clarity"


@dataclass
class PromptVariation:
    """A prompt variation with metadata."""
    id: str
    content: str
    mutation_type: MutationType
    parent_ids: List[str] = field(default_factory=list)
    generation: int = 0
    fitness_score: float = 0.0
    dimension_scores: Dict[FitnessDimension, float] = field(default_factory=dict)
    test_results: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    token_count: int = 0


@dataclass
class TestCase:
    """Test case for evaluating prompts."""
    input_data: Dict[str, Any]
    expected_output: Any
    edge_case: bool = False
    weight: float = 1.0


@dataclass
class Generation:
    """A generation in the evolutionary process."""
    number: int
    population: List[PromptVariation]
    best_fitness: float
    average_fitness: float
    diversity_score: float
    timestamp: datetime = field(default_factory=datetime.now)


class PromptMutator:
    """Generates prompt variations through various mutation strategies."""

    def __init__(self):
        self.mutation_strategies = {
            MutationType.REPHRASE: self._mutate_rephrase,
            MutationType.CONTEXT_MODIFY: self._mutate_context,
            MutationType.FORMALITY_ADJUST: self._mutate_formality,
            MutationType.RESTRUCTURE: self._mutate_restructure,
            MutationType.EXAMPLE_FORMAT: self._mutate_examples,
            MutationType.DIRECTIVE_STRENGTH: self._mutate_directives,
            MutationType.CONSTRAINT_MODIFY: self._mutate_constraints,
            MutationType.SPECIFICITY_ADJUST: self._mutate_specificity,
            MutationType.CROSS_POLLINATE: self._mutate_cross_pollinate,
            MutationType.CREATIVE_RANDOM: self._mutate_creative
        }

    async def generate_variations(
        self,
        base_prompt: str,
        num_variations: int = 10,
        high_performers: Optional[List[PromptVariation]] = None
    ) -> List[PromptVariation]:
        """Generate prompt variations using different mutation strategies."""
        variations = []

        # Apply each mutation type
        for i, mutation_type in enumerate(MutationType):
            if i >= num_variations:
                break

            strategy = self.mutation_strategies[mutation_type]
            varied_content = await strategy(base_prompt, high_performers)

            variation = PromptVariation(
                id=self._generate_id(varied_content),
                content=varied_content,
                mutation_type=mutation_type,
                token_count=len(varied_content.split())  # Simplified
            )
            variations.append(variation)

        return variations

    async def _mutate_rephrase(self, prompt: str, high_performers: Optional[List[PromptVariation]]) -> str:
        """Rephrase instructions while maintaining meaning."""
        # Simulate rephrasing key phrases
        replacements = {
            "you must": random.choice(["it is essential to", "you need to", "ensure you"]),
            "analyze": random.choice(["examine", "investigate", "evaluate"]),
            "provide": random.choice(["supply", "deliver", "present"]),
            "consider": random.choice(["take into account", "think about", "factor in"]),
            "important": random.choice(["crucial", "vital", "key"]),
            "should": random.choice(["ought to", "need to", "must"]),
            "create": random.choice(["generate", "produce", "develop"]),
            "identify": random.choice(["find", "locate", "determine"])
        }

        result = prompt
        for old, new in replacements.items():
            if old in result.lower():
                result = re.sub(rf'\b{old}\b', new, result, flags=re.IGNORECASE)

        return result

    async def _mutate_context(self, prompt: str, high_performers: Optional[List[PromptVariation]]) -> str:
        """Add or remove context details."""
        lines = prompt.split('\n')

        if random.random() < 0.5 and len(lines) > 3:
            # Remove context (make more concise)
            remove_phrases = ["for example", "such as", "in other words", "that is"]
            result = prompt
            for phrase in remove_phrases:
                result = re.sub(rf'{phrase}[^.]*\.', '.', result, flags=re.IGNORECASE)
            return result
        else:
            # Add context
            additions = [
                "\nConsider all relevant factors and dependencies.",
                "\nBe thorough in your analysis.",
                "\nProvide specific examples where applicable.",
                "\nEnsure completeness and accuracy."
            ]
            return prompt + random.choice(additions)

    async def _mutate_formality(self, prompt: str, high_performers: Optional[List[PromptVariation]]) -> str:
        """Adjust formality level."""
        if random.random() < 0.5:
            # Make more formal
            replacements = {
                "don't": "do not",
                "can't": "cannot",
                "won't": "will not",
                "you'll": "you will",
                "let's": "let us",
                "gonna": "going to",
                "wanna": "want to"
            }
        else:
            # Make less formal
            replacements = {
                "do not": "don't",
                "cannot": "can't",
                "will not": "won't",
                "you will": "you'll",
                "let us": "let's"
            }

        result = prompt
        for old, new in replacements.items():
            result = result.replace(old, new)

        return result

    async def _mutate_restructure(self, prompt: str, high_performers: Optional[List[PromptVariation]]) -> str:
        """Restructure information order."""
        # Split into sentences
        sentences = [s.strip() for s in prompt.split('.') if s.strip()]

        if len(sentences) > 2:
            # Shuffle middle sentences, keep first and last
            if len(sentences) > 3:
                middle = sentences[1:-1]
                random.shuffle(middle)
                sentences = [sentences[0]] + middle + [sentences[-1]]
            else:
                random.shuffle(sentences)

        return '. '.join(sentences) + '.'

    async def _mutate_examples(self, prompt: str, high_performers: Optional[List[PromptVariation]]) -> str:
        """Modify example format."""
        if "example:" in prompt.lower():
            # Change example format
            formats = [
                "For instance: ",
                "E.g., ",
                "Sample: ",
                "Like this: ",
                "Here's how: "
            ]
            return re.sub(r'example:', random.choice(formats), prompt, flags=re.IGNORECASE)
        else:
            # Add an example structure
            return prompt + "\n\nProvide concrete examples to illustrate your response."

    async def _mutate_directives(self, prompt: str, high_performers: Optional[List[PromptVariation]]) -> str:
        """Change directive strength."""
        strong_to_weak = {
            "must": "should",
            "always": "generally",
            "never": "avoid",
            "essential": "important",
            "require": "recommend"
        }

        weak_to_strong = {v: k for k, v in strong_to_weak.items()}

        # Randomly choose direction
        if random.random() < 0.5:
            replacements = strong_to_weak
        else:
            replacements = weak_to_strong

        result = prompt
        for old, new in replacements.items():
            if old in result.lower():
                result = re.sub(rf'\b{old}\b', new, result, flags=re.IGNORECASE)

        return result

    async def _mutate_constraints(self, prompt: str, high_performers: Optional[List[PromptVariation]]) -> str:
        """Add or remove constraints."""
        if random.random() < 0.5:
            # Add constraints
            constraints = [
                "\nLimit your response to the most relevant points.",
                "\nBe concise and to the point.",
                "\nFocus on practical applications.",
                "\nPrioritize accuracy over comprehensiveness."
            ]
            return prompt + random.choice(constraints)
        else:
            # Remove constraints if present
            remove_patterns = [
                r'limit[^.]*\.',
                r'concise[^.]*\.',
                r'brief[^.]*\.',
                r'short[^.]*\.'
            ]
            result = prompt
            for pattern in remove_patterns:
                result = re.sub(pattern, '', result, flags=re.IGNORECASE)
            return result.strip()

    async def _mutate_specificity(self, prompt: str, high_performers: Optional[List[PromptVariation]]) -> str:
        """Adjust specificity level."""
        if random.random() < 0.5:
            # Make more specific
            additions = [
                " Be explicit about your reasoning process.",
                " Include step-by-step details.",
                " Specify exact criteria used.",
                " Provide precise measurements or metrics."
            ]
            return prompt + random.choice(additions)
        else:
            # Make more general
            result = re.sub(r'specifically|exactly|precisely', 'generally', prompt, flags=re.IGNORECASE)
            result = re.sub(r'step.by.step|detailed', 'overall', result, flags=re.IGNORECASE)
            return result

    async def _mutate_cross_pollinate(self, prompt: str, high_performers: Optional[List[PromptVariation]]) -> str:
        """Cross-pollinate with high-performing prompts."""
        if not high_performers:
            return prompt

        # Take elements from high performers
        donor = random.choice(high_performers)
        donor_sentences = donor.content.split('.')
        current_sentences = prompt.split('.')

        if donor_sentences and current_sentences:
            # Replace a random sentence with one from donor
            if len(current_sentences) > 1 and len(donor_sentences) > 1:
                idx = random.randint(0, len(current_sentences) - 1)
                donor_idx = random.randint(0, len(donor_sentences) - 1)
                current_sentences[idx] = donor_sentences[donor_idx]

        return '.'.join(current_sentences)

    async def _mutate_creative(self, prompt: str, high_performers: Optional[List[PromptVariation]]) -> str:
        """Apply random creative variations."""
        strategies = [
            lambda p: "Let's think step by step. " + p,
            lambda p: p + " Explain your reasoning.",
            lambda p: "As an expert, " + p,
            lambda p: p.replace(".", ".\n") if p.count(".") > 2 else p,
            lambda p: f"Context: You are solving a complex problem.\n\n{p}",
            lambda p: p + "\n\nDouble-check your work for accuracy.",
            lambda p: f"Important: {p}",
            lambda p: re.sub(r'\?', '? Please be thorough.', p)
        ]

        strategy = random.choice(strategies)
        return strategy(prompt)

    def _generate_id(self, content: str) -> str:
        """Generate unique ID for prompt variation."""
        return hashlib.md5(content.encode()).hexdigest()[:8]


class FitnessEvaluator:
    """Evaluates prompt fitness across multiple dimensions."""

    def __init__(self, base_agent: Optional[BaseAgent] = None):
        self.base_agent = base_agent or BaseAgent(role="evaluator", model="claude-3-5-sonnet-20241022")

    async def evaluate(
        self,
        variation: PromptVariation,
        test_cases: List[TestCase]
    ) -> Tuple[float, Dict[FitnessDimension, float]]:
        """Evaluate a prompt variation on test cases."""
        dimension_scores = {
            FitnessDimension.ACCURACY: 0.0,
            FitnessDimension.CONSISTENCY: 0.0,
            FitnessDimension.EFFICIENCY: 0.0,
            FitnessDimension.ROBUSTNESS: 0.0,
            FitnessDimension.CLARITY: 0.0
        }

        # Run test cases
        results = []
        for test_case in test_cases:
            result = await self._run_test_case(variation, test_case)
            results.append(result)

        # Calculate dimension scores
        dimension_scores[FitnessDimension.ACCURACY] = self._calculate_accuracy(results)
        dimension_scores[FitnessDimension.CONSISTENCY] = self._calculate_consistency(results)
        dimension_scores[FitnessDimension.EFFICIENCY] = self._calculate_efficiency(variation, results)
        dimension_scores[FitnessDimension.ROBUSTNESS] = self._calculate_robustness(results, test_cases)
        dimension_scores[FitnessDimension.CLARITY] = self._calculate_clarity(variation)

        # Calculate overall fitness (weighted average)
        weights = {
            FitnessDimension.ACCURACY: 0.35,
            FitnessDimension.CONSISTENCY: 0.20,
            FitnessDimension.EFFICIENCY: 0.15,
            FitnessDimension.ROBUSTNESS: 0.20,
            FitnessDimension.CLARITY: 0.10
        }

        overall_fitness = sum(
            score * weights[dim]
            for dim, score in dimension_scores.items()
        )

        # Update variation
        variation.fitness_score = overall_fitness
        variation.dimension_scores = dimension_scores
        variation.test_results = results

        return overall_fitness, dimension_scores

    async def _run_test_case(
        self,
        variation: PromptVariation,
        test_case: TestCase
    ) -> Dict[str, Any]:
        """Run a single test case."""
        # Simulate running the prompt
        # In real implementation, would call the actual LLM

        # Simulate performance metrics
        success = random.random() > 0.3  # 70% success rate baseline

        # Adjust based on mutation type (some are better)
        if variation.mutation_type in [MutationType.REPHRASE, MutationType.RESTRUCTURE]:
            success = random.random() > 0.25  # Slightly better
        elif variation.mutation_type == MutationType.CREATIVE_RANDOM:
            success = random.random() > 0.4  # More variable

        return {
            "success": success,
            "latency_ms": random.randint(100, 500),
            "tokens_used": variation.token_count + random.randint(-10, 20),
            "confidence": random.random(),
            "test_case": test_case
        }

    def _calculate_accuracy(self, results: List[Dict[str, Any]]) -> float:
        """Calculate accuracy score."""
        if not results:
            return 0.0

        successes = sum(1 for r in results if r["success"])
        return successes / len(results)

    def _calculate_consistency(self, results: List[Dict[str, Any]]) -> float:
        """Calculate consistency score."""
        if len(results) < 2:
            return 1.0

        # Check variance in confidence scores
        confidences = [r["confidence"] for r in results]
        if confidences:
            variance = statistics.variance(confidences) if len(confidences) > 1 else 0
            # Lower variance = higher consistency
            return max(0, 1 - variance)

        return 0.5

    def _calculate_efficiency(
        self,
        variation: PromptVariation,
        results: List[Dict[str, Any]]
    ) -> float:
        """Calculate efficiency score."""
        if not results:
            return 0.0

        # Average latency and token usage
        avg_latency = statistics.mean([r["latency_ms"] for r in results])
        avg_tokens = statistics.mean([r["tokens_used"] for r in results])

        # Normalize (lower is better)
        latency_score = max(0, 1 - (avg_latency / 1000))  # Normalize to 1 second
        token_score = max(0, 1 - (avg_tokens / 200))  # Normalize to 200 tokens

        return (latency_score + token_score) / 2

    def _calculate_robustness(
        self,
        results: List[Dict[str, Any]],
        test_cases: List[TestCase]
    ) -> float:
        """Calculate robustness score (performance on edge cases)."""
        edge_case_results = [
            r for r in results
            if r["test_case"].edge_case
        ]

        if not edge_case_results:
            # No edge cases to test
            return self._calculate_accuracy(results)

        edge_successes = sum(1 for r in edge_case_results if r["success"])
        return edge_successes / len(edge_case_results)

    def _calculate_clarity(self, variation: PromptVariation) -> float:
        """Calculate clarity score based on prompt structure."""
        content = variation.content

        # Factors that improve clarity
        clarity_score = 0.5  # Base score

        # Clear structure (numbered points, bullets)
        if any(pattern in content for pattern in ['1.', '•', '-', '*']):
            clarity_score += 0.1

        # Appropriate length (not too long or short)
        word_count = len(content.split())
        if 20 <= word_count <= 150:
            clarity_score += 0.2
        elif word_count < 20:
            clarity_score -= 0.1
        else:  # Too long
            clarity_score -= 0.2

        # Contains clear directives
        directives = ['please', 'ensure', 'must', 'should', 'need']
        if any(d in content.lower() for d in directives):
            clarity_score += 0.1

        # Has examples
        if 'example' in content.lower() or 'e.g.' in content.lower():
            clarity_score += 0.1

        return max(0, min(1, clarity_score))


class GeneticSelector:
    """Applies genetic algorithms for prompt evolution."""

    def __init__(
        self,
        population_size: int = 50,
        elite_ratio: float = 0.3,
        breeding_ratio: float = 0.4,
        mutation_rate: float = 0.2,
        innovation_ratio: float = 0.1
    ):
        self.population_size = population_size
        self.elite_ratio = elite_ratio
        self.breeding_ratio = breeding_ratio
        self.mutation_rate = mutation_rate
        self.innovation_ratio = innovation_ratio
        self.mutator = PromptMutator()

    async def evolve_generation(
        self,
        current_generation: List[PromptVariation],
        generation_number: int
    ) -> List[PromptVariation]:
        """Evolve to next generation using genetic algorithm."""

        # Sort by fitness
        sorted_population = sorted(
            current_generation,
            key=lambda x: x.fitness_score,
            reverse=True
        )

        next_generation = []

        # 1. Elite selection (top performers preserved)
        elite_count = int(len(sorted_population) * self.elite_ratio)
        elite = sorted_population[:elite_count]
        for prompt in elite:
            prompt.generation = generation_number
        next_generation.extend(elite)

        # 2. Breeding (crossover)
        breeding_count = int(len(sorted_population) * self.breeding_ratio)
        breeding_pool = sorted_population[:breeding_count * 2]  # Top candidates

        for _ in range(breeding_count):
            parent1, parent2 = random.sample(breeding_pool, 2)
            offspring = await self._crossover(parent1, parent2)
            offspring.generation = generation_number
            next_generation.append(offspring)

        # 3. Mutation of offspring
        mutation_candidates = next_generation[elite_count:]  # Don't mutate elite
        for candidate in mutation_candidates:
            if random.random() < self.mutation_rate:
                mutated = await self._mutate(candidate)
                mutated.generation = generation_number
                # Replace original with mutated version
                idx = next_generation.index(candidate)
                next_generation[idx] = mutated

        # 4. Innovation (completely new variants)
        innovation_count = int(self.population_size * self.innovation_ratio)

        # Use best performer as base for innovations
        best_performer = sorted_population[0]
        innovations = await self.mutator.generate_variations(
            best_performer.content,
            innovation_count,
            elite
        )

        for innovation in innovations:
            innovation.generation = generation_number

        next_generation.extend(innovations)

        # 5. Fill remaining slots with mutations of top performers
        while len(next_generation) < self.population_size:
            source = random.choice(elite)
            mutated = await self._mutate(source)
            mutated.generation = generation_number
            next_generation.append(mutated)

        # Ensure we don't exceed population size
        return next_generation[:self.population_size]

    async def _crossover(
        self,
        parent1: PromptVariation,
        parent2: PromptVariation
    ) -> PromptVariation:
        """Crossover two parent prompts to create offspring."""
        # Split parents into segments
        p1_sentences = parent1.content.split('.')
        p2_sentences = parent2.content.split('.')

        # Combine segments from both parents
        offspring_sentences = []
        max_len = max(len(p1_sentences), len(p2_sentences))

        for i in range(max_len):
            if i < len(p1_sentences) and i < len(p2_sentences):
                # Randomly choose from either parent
                offspring_sentences.append(
                    random.choice([p1_sentences[i], p2_sentences[i]])
                )
            elif i < len(p1_sentences):
                offspring_sentences.append(p1_sentences[i])
            else:
                offspring_sentences.append(p2_sentences[i])

        offspring_content = '.'.join(offspring_sentences)

        return PromptVariation(
            id=self.mutator._generate_id(offspring_content),
            content=offspring_content,
            mutation_type=MutationType.CROSS_POLLINATE,
            parent_ids=[parent1.id, parent2.id],
            token_count=len(offspring_content.split())
        )

    async def _mutate(self, variation: PromptVariation) -> PromptVariation:
        """Apply mutation to a prompt variation."""
        # Choose random mutation type
        mutation_type = random.choice(list(MutationType))

        # Apply mutation
        mutated_variations = await self.mutator.generate_variations(
            variation.content,
            1,
            None
        )

        if mutated_variations:
            mutated = mutated_variations[0]
            mutated.parent_ids = [variation.id]
            mutated.mutation_type = mutation_type
            return mutated

        return variation

    def calculate_diversity(self, population: List[PromptVariation]) -> float:
        """Calculate genetic diversity of population."""
        if len(population) < 2:
            return 0.0

        # Calculate pairwise similarity
        similarities = []
        for i in range(len(population)):
            for j in range(i + 1, len(population)):
                sim = self._calculate_similarity(
                    population[i].content,
                    population[j].content
                )
                similarities.append(sim)

        if similarities:
            # Diversity is inverse of average similarity
            avg_similarity = statistics.mean(similarities)
            return 1 - avg_similarity

        return 0.5

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0


class PromptEvolutionEngine:
    """Main engine for evolving prompts over generations."""

    def __init__(
        self,
        population_size: int = 50,
        max_generations: int = 100,
        target_fitness: float = 0.95
    ):
        self.population_size = population_size
        self.max_generations = max_generations
        self.target_fitness = target_fitness

        self.mutator = PromptMutator()
        self.evaluator = FitnessEvaluator()
        self.selector = GeneticSelector(population_size=population_size)

        self.generations: List[Generation] = []
        self.best_prompt: Optional[PromptVariation] = None
        self.evolution_history: List[Dict[str, Any]] = []

    async def evolve(
        self,
        base_prompt: str,
        test_cases: List[TestCase],
        max_generations: Optional[int] = None
    ) -> PromptVariation:
        """Evolve a prompt over multiple generations."""
        max_gens = max_generations or self.max_generations

        # Initialize first generation
        print(f"🧬 Initializing population of {self.population_size} prompts...")
        current_population = await self._initialize_population(base_prompt)

        for generation_num in range(max_gens):
            print(f"\n📊 Generation {generation_num + 1}/{max_gens}")

            # Evaluate fitness
            await self._evaluate_population(current_population, test_cases)

            # Track generation
            best = max(current_population, key=lambda x: x.fitness_score)
            worst = min(current_population, key=lambda x: x.fitness_score)
            avg_fitness = statistics.mean([p.fitness_score for p in current_population])
            diversity = self.selector.calculate_diversity(current_population)

            generation = Generation(
                number=generation_num,
                population=current_population,
                best_fitness=best.fitness_score,
                average_fitness=avg_fitness,
                diversity_score=diversity
            )
            self.generations.append(generation)

            # Update best
            if self.best_prompt is None or best.fitness_score > self.best_prompt.fitness_score:
                self.best_prompt = best

            print(f"  Best fitness: {best.fitness_score:.3f}")
            print(f"  Avg fitness: {avg_fitness:.3f}")
            print(f"  Worst fitness: {worst.fitness_score:.3f}")
            print(f"  Diversity: {diversity:.3f}")

            # Check termination conditions
            if best.fitness_score >= self.target_fitness:
                print(f"✅ Target fitness {self.target_fitness} achieved!")
                break

            # Evolve to next generation
            current_population = await self.selector.evolve_generation(
                current_population,
                generation_num + 1
            )

        return self.best_prompt

    async def _initialize_population(self, base_prompt: str) -> List[PromptVariation]:
        """Initialize the first generation."""
        population = []

        # Add original
        original = PromptVariation(
            id=self.mutator._generate_id(base_prompt),
            content=base_prompt,
            mutation_type=MutationType.REPHRASE,  # Placeholder
            generation=0,
            token_count=len(base_prompt.split())
        )
        population.append(original)

        # Generate variations
        while len(population) < self.population_size:
            variations = await self.mutator.generate_variations(
                base_prompt,
                self.population_size - len(population)
            )
            population.extend(variations)

        return population[:self.population_size]

    async def _evaluate_population(
        self,
        population: List[PromptVariation],
        test_cases: List[TestCase]
    ):
        """Evaluate fitness of entire population."""
        for variation in population:
            if variation.fitness_score == 0:  # Not yet evaluated
                await self.evaluator.evaluate(variation, test_cases)

    def get_evolution_report(self) -> Dict[str, Any]:
        """Generate comprehensive evolution report."""
        if not self.generations:
            return {"status": "No evolution performed yet"}

        return {
            "total_generations": len(self.generations),
            "best_prompt": {
                "content": self.best_prompt.content,
                "fitness": self.best_prompt.fitness_score,
                "generation": self.best_prompt.generation,
                "mutation_type": self.best_prompt.mutation_type.value,
                "dimensions": {
                    dim.value: score
                    for dim, score in self.best_prompt.dimension_scores.items()
                }
            },
            "evolution_curve": [
                {
                    "generation": g.number,
                    "best_fitness": g.best_fitness,
                    "avg_fitness": g.average_fitness,
                    "diversity": g.diversity_score
                }
                for g in self.generations
            ],
            "improvement": {
                "start_fitness": self.generations[0].best_fitness,
                "end_fitness": self.generations[-1].best_fitness,
                "percent_improvement": (
                    (self.generations[-1].best_fitness - self.generations[0].best_fitness)
                    / self.generations[0].best_fitness * 100
                )
            }
        }


# Convenience function for quick evolution
async def evolve_prompt(
    base_prompt: str,
    test_cases: Optional[List[TestCase]] = None,
    generations: int = 20
) -> Tuple[str, Dict[str, Any]]:
    """Quick function to evolve a prompt."""

    # Default test cases if none provided
    if test_cases is None:
        test_cases = [
            TestCase({"input": "test1"}, "expected1", edge_case=False),
            TestCase({"input": "test2"}, "expected2", edge_case=False),
            TestCase({"input": "edge1"}, "edge_expected", edge_case=True),
        ]

    engine = PromptEvolutionEngine(
        population_size=30,
        max_generations=generations,
        target_fitness=0.9
    )

    best = await engine.evolve(base_prompt, test_cases)
    report = engine.get_evolution_report()

    return best.content, report


if __name__ == "__main__":
    # Demo
    async def demo():
        base = "Analyze the provided text and identify key themes."

        print("🧬 Starting Prompt Evolution Demo")
        print("=" * 50)
        print(f"Base prompt: {base}")
        print("=" * 50)

        evolved, report = await evolve_prompt(base, generations=10)

        print(f"\n✨ Evolved prompt:")
        print(evolved)
        print(f"\n📊 Evolution Report:")
        print(f"  Fitness improved: {report['improvement']['percent_improvement']:.1f}%")
        print(f"  Final fitness: {report['best_prompt']['fitness']:.3f}")
        print(f"  Best dimensions:")
        for dim, score in report['best_prompt']['dimensions'].items():
            print(f"    {dim}: {score:.3f}")

    asyncio.run(demo())