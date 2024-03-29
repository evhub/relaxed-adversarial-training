_This post is part of research I did at OpenAI with mentoring and guidance from Paul Christiano. It also represents my current agenda regarding what I believe is the best approach for addressing [inner alignment](https://arxiv.org/abs/1906.01820)._

One particularly concerning failure mode for any sort of advanced AI system is for it to have good performance on the training distribution, but nevertheless still have some input on which it behaves highly “unacceptably” during deployment. For the purposes of this post, we will [follow Paul Christiano](https://ai-alignment.com/training-robust-corrigibility-ce0e0a3b9b4d) in thinking about acceptability as some concept that satisfies the following two conditions:

1. “As long as the model _always_ behaves acceptably, and achieves a high reward on _average_, we can be happy.”
2. “Requiring a model to always behave acceptably wouldn't make a hard problem too much harder.”

Thus, acceptability is a different condition than asking for good performance during deployment—an honest mistake is considered acceptable, as is just failing to do anything interesting at all. That being said, some of the sorts of things you might want from acceptability could include [corrigibility](https://ai-alignment.com/corrigibility-3039e668638), [non-deception](https://www.alignmentforum.org/s/r9tYkB2a8Fp4DN8yB/p/zthDPAjh9w6Ytbeks), or myopia.[^1] The hope for this style of approach is that it is competitive to only apply advanced machine learning to those situations which have clear notions of acceptability.

[^1]: For a further treatment of the question of what a good acceptability guarantee might look like, see “[Towards a mechanistic understanding of corrigibility](https://www.alignmentforum.org/posts/BKM8uQS6QdJPZLqCr/towards-a-mechanistic-understanding-of-corrigibility).”

The tension, however, rests in being able to achieve good performance while maintaining an acceptability guarantee. Thus, the ideal solution to this problem would be a way of converting a training procedure which can achieve arbitrary performance into a training procedure which is not much harder to run, and which can still achieve arbitrary performance, but which also enforces an acceptability guarantee.

One obvious way to attempt to maintain an acceptability guarantee is to construct a loss function which incentivizes acceptability as part of performance. Something of this form is almost certainly going to be a component of any safe system. That being said, there are some reasons why approaches of this form might be insufficient if used in isolation.

First, one important thing to note about folding acceptability into performance is that the resulting acceptability guarantee is fairly weak: you get an average-case acceptability guarantee that holds only in the case of no distributional shift, with no guarantee when your deployment distribution is different than your training distribution.[^2]

[^2]: See the “Hard cases” section for an analysis of ways in which a guarantee of this form might be insufficient and/or difficult to obtain.

Second, there are reasons to believe that the objective of a model doing some sort of internal planning/search might be systematically different than its loss function. Thus, even if the loss function incentivizes acceptability, the training process's inductive biases might be such that the model ends up not actually optimizing for an acceptable objective. This is the problem “[Risks from Learned Optimization](https://arxiv.org/abs/1906.01820)” refers to as inner alignment,[^3] though other frameworks have also been proposed for understanding this sort of phenomenon. [Ortega et al. recently presented in a DeepMind Technical Report](https://arxiv.org/abs/1905.03030), for example, an analysis of this problem from the perspective of treating it as spontaneous meta-learning, noting that:

[^3]: Note that there are still a lot of unresolved open questions regarding inner alignment. “[Risks from Learned Optimization](https://arxiv.org/abs/1906.01820)” attempts to address many of these questions from a theoretical perspective, though additional [experimental evidence](https://www.alignmentforum.org/posts/uSdPa9nrSgmXCtdKN/concrete-experiments-in-inner-alignment) would also be useful to further pin down this problem.

> “Meta-learning can also occur spontaneously in online regression when the capacity of the agent is bounded and the data is produced by a single generator. Unfortunately, the downside is that we cannot easily control what will be metalearned. In particular, spontaneous meta-learning could lead to undesirable emergent properties, which is considered an open research problem in AI safety [[Ortega et al., 2018]](https://medium.com/@deepmindsafetyresearch/building-safe-artificial-intelligence-52f5f75058f1).”

The key problem that arises in this sort of situation is that it raises the possibility of [capability generalization without objective generalization](https://www.alignmentforum.org/posts/2mhFMgtAjFJesaSYR/2-d-robustness). That is, for a model doing some sort of search/meta-learning, it might be that its search algorithm generalizes well off-distribution such that it continues being able to take competent, well-optimized actions, but that the objective its search is directed towards fails to generalize such that those actions are now optimized for the wrong objective.

Finally, there are reasons that we might want to consider the possibility of near-AGI models learning to deceive their training processes. The full argument for why this might be the case is given in the section on deceptive alignment in “[Risks from Learned Optimization](https://arxiv.org/abs/1906.01820),” but the basic concern is that a model could learn about the true reward via its input and thus start appearing aligned for the purpose of sticking around in the training process before gradient descent has the chance to modify it to actually optimize for the true reward internally.

&nbsp;

## Background

If incentivizing acceptability as part of performance is insufficient, as it seems it might be, then a better solution for enforcing acceptability guarantees is required. [One framework Paul has proposed](https://ai-alignment.com/training-robust-corrigibility-ce0e0a3b9b4d) is to attempt to make use of adversarial training, wherein you could train an adversary to find inputs on which the model behaves unacceptability and then penalize it accordingly. The goal of this post is to explore this avenue as thoroughly as possible.

One initial roadblock with this approach, however, is that there might exist some inputs on which the model behaves unacceptably which are difficult to instantiate during training—future situations that cannot be predicted in complete detail, for example.[^4] [Paul's proposed solution](https://ai-alignment.com/training-robust-corrigibility-ce0e0a3b9b4d) to this problem is to relax the adversary's job. Rather than asking the adversary to instantiate a concrete input on which the model behaves unacceptably, we can instead just ask the adversary to produce some sort of description of such a situation, which we will call a pseudo-input. Paul proposes the following two conditions as the major desiderata for any pseudo-input-based approach:

[^4]: See the “Conditional defection” hard case for more examples of inputs that might lead to unacceptable behavior which might be very difficult to instantiate during training.

1. “It's still ‘easy enough' for the agent to never behave unacceptably for any pseudo-input.”
2. “It's easy for the adversary to find a pseudo-input on which the agent behaves unacceptably, if any exist.”

Under Paul's framework, the structure of pseudo-inputs has to be constrained so that “an input that contains X” is a valid pseudo-input but “a distribution over inputs that would cause the agent to want to kill everyone” is not. That way, the model's task of steering clear of having any pseudo-inputs on which it behaves badly is actually potentially soluble.

&nbsp;

## Formalization

We'll start by formalizing Paul's approach so we can use it as a starting point. Let $\mathbb X$ be the space of possible states (which we will assume includes any question we want to ask the model as a state), $\mathbb A$ be the space of possible actions, $M: \mathbb X \to \mathbb A$ be the model, $\mathbb M$ be the space of all possible models, $\text{Amp}: \mathbb M \to \mathbb M$ be some amplification operation,[^5] and $\mathbb X_\text{pseudo}$ be the space of possible pseudo-inputs. Then, [as per Paul's proposal](https://ai-alignment.com/training-robust-corrigibility-ce0e0a3b9b4d), we'll implement

[^5]: This could be pure supervised amplification, debate, or anything in-between. For simplicity, I mostly think about the pure supervised case wherein $\text{Amp}(M)$ is implemented simply by asking the question to a human with the ability to consult the model.

our adversary $\text{Adv}: \mathbb M \to \mathbb X_\text{pseudo}$ as
$$\begin{align*}
    \text{Adv}(M) = \text{Amp}(M)(&\text{“What's a pseudo-input on which } M \text{ is particularly} \\
    & \text{likely to recommend an unacceptable action?”}),
\end{align*}$$
our unacceptability checker $C: \mathbb M \times \mathbb X_\text{pseudo} \to \mathbb B$ as
$$
    C(M, \alpha) = \text{Amp}(M)(\text{“Is model } M \text{ unacceptable on pseudo-input } \alpha \text{?”}),
$$
and finally our model's unacceptability penalty as
$$
    L_M = C(M, \text{Adv}(M)).
$$

That's our starting point, but can we do better? One initial observation is that this approach relies heavily on constraining $\mathbb X_\text{pseudo}$ to exclude the sorts of pseudo-inputs that the model shouldn't have to deal with such as “a distribution over inputs such that $M$ kills all humans.” If we want to allow very general pseudo-inputs, however, then this constraint might not be very natural to implement. Furthermore, it's unclear that a binary constraint is actually what we want here: we care significantly more about pseudo-inputs that are more likely to come up during deployment.[^6] In fact, if we think of pseudo-inputs as predicates that constrain $\mathbb X$, we can approximate the probability of unacceptable behavior during deployment as[^16]

[^16]: Note that this approximation is tight if and only if there exists some $\alpha \in \mathbb X_\text{pseudo}$ such that $\alpha(x) \leftrightarrow C(M, x)$.

[^6]: Note that this still assumes $C$ is binary—which is not quite right since we might care about some unacceptable actions more than others—though that can also easily be relaxed by moving to an expectation rather than a probability.

$$\begin{align*}
    \mathbb P(C(M, x) \ |\ x \sim \text{deploy}) \approx \max_{\alpha \in \mathbb X_\text{pseudo}} & \mathbb P(\alpha(x) \ |\ x \sim \text{deploy}) \\
    & \cdot\ \mathbb P(C(M, x) \ |\ \alpha(x),~ x \sim \text{deploy})
\end{align*}$$
such that, if we can get a good implementation of $\mathbb P$, we no longer have to worry as much about carefully constraining $\mathbb X_\text{pseudo}$, as we can just let $\mathbb P$'s prior do that work for us. Thus, we'll define[^7]

[^7]: One concern with this definition is that probabilities are not in general well-defined over logical statements. To resolve this problem, we can instead ask something of the form “What is your break-even price for a contract that pays out \$1 if $A$ and $B$ are true but that is fully refunded if $B$ is false?”

$$
    P_M(A|B) = \text{Amp}(M)(\text{“What is the probability of } A \text{ conditional on } B \text{?”})
$$
such that we get the new unacceptability penalty[^8]

[^8]: Alternatively, if we want to think of deployment as a concrete set of inputs $\mathbb X_\text{deploy}$ rather than a distribution, we can set $L_M = P_M(\exists x \in \mathbb X_\text{deploy},~ \text{Adv}(M)(x)) \cdot P_M(\exists x \in \mathbb X_\text{deploy},~ \text{Adv}(M)(x) \to C(M, x))$.

$$
    L_M = P_M(\text{Adv}(M)(x) \ |\ x \sim \text{deploy}) \cdot P_M(C(M, x) \ |\ \text{Adv}(M)(x),~ x \sim \text{deploy})
$$
which is the primary model I'll be working with for the rest of this post.

&nbsp;

## Hard cases

Now that we have our model, we'll look at some of the hard cases that have to be solved for any sort of approach of this form to go through.

**Random unacceptability.** One of the simplest examples of an unacceptable model is one that simply has some low probability of unacceptability such that it is difficult to pick up on training but still possible to see during deployment. If you can guarantee that model samples will be independently and identically distributed (iid), and you have an average case performance guarantee over some metric that includes acceptability, then you might hope to get an average case acceptability guarantee which can mitigate such a case of low probability unacceptable behavior. However, it is unclear exactly how difficult getting an iid guarantee might be as well as how good the resulting acceptability guarantee would be. As a simple model, suppose there are $n$ training steps and $m$ deployment steps. Then, let $p$ be the probability that our model behaves acceptably at each step, where we will assume that steps are iid. Then, we want to know the probability of unacceptable behavior during deployment given weak assumptions on $p$ other than that we know it was acceptable during training. Thus, if we adopt a uniform prior[^9] over $p$ and update on seeing $n$ instances of acceptable behavior, we get the posterior $p \sim \text{Beta}(n+1,~ 1)$, which yields the overall probability of unacceptable behavior during deployment of

[^9]: Note that this is a conservative prior. In practice, we might hope for random unacceptable behavior to be unlikely enough and difficult enough that we can get a significant advantage out of our prior rather than simply assuming uniformity.

$$
    \mathbb P(\exists x \in \mathbb X_\text{deploy},~ C(M, x)) = \frac{m}{m + n + 1}.
$$
Thus, if we have an iid guarantee and we limit ourselves only to cases where $m \ll n$, we're likely to be fairly safe.

However, $m \ll n$ is a hard condition to satisfy[^10] —can we do better? In particular, what happens if we can deal with one instance of unacceptable behavior, but not multiple? We will consider two possible models: in the sequential model, it takes $d$ sequential instances of unacceptable behavior during deployment to be unacceptable, whereas in the non-sequential model it takes $d$ instances of unacceptable behavior at any time during deployment to be unacceptable. Then, let $\epsilon$ be the probability of unacceptable deployment in the original model, $\epsilon_{d\text{ seq}}$ be the probability of an unacceptable deployment in the sequential model, and $\epsilon_{d\text{ non-seq}}$ be the equivalent for the non-sequential model. Then, running a series of experiments using [iterative black-box optimization](https://github.com/evhub/iternash) to perform a maximum likelihood estimate,[^17] we get[^18]

[^18]: The trends given here are highly approximate. Significantly better approximations are given by $\epsilon_{d\text{ non-seq}} \approx \epsilon^d \cdot 2^{(d-1)(d+6)/10}$ and $\epsilon_{d\text{ seq}} \approx \epsilon^d \cdot m^{1-d} \cdot 2^{(d-1)(d+4)/3}$.

[^17]: Specifically, the experiments were conducted by using a black-box optimizer to select $p^*$ so as to maximize $\mathbb P(\text{Bin}(n, p^*) = n) \cdot \mathbb P(\exists x \in \mathbb X_\text{deploy},~ C(M, x)\ |\ p = p^*)$.

[^10]: One appealing idea for how we might be able to satisfy it is if we use some sort of online learning scheme. This doesn't actually solve the problem, however—the difference between $n$ and $m$ here is just that unacceptable behavior in $n$ is recoverable but unacceptable behavior in $m$ is not. Even if we do online learning, the system will presumably still have to be deployed in situations where it will be able to take actions that would be unrecoverable if unacceptable. However, online learning might help us increase the number of unacceptable actions required before the situation becomes unrecoverable, which is exactly the fix analyzed here.

$$\begin{align*}
    \epsilon_{d\text{ non-seq}} &\approx \epsilon^d \\
    \epsilon_{d\text{ seq}} &\approx \frac{\epsilon^d}{m^{d-1}}.
\end{align*}$$
Thus, if we can manage to be in one of these regimes, we can get a significantly better acceptability guarantee, making it possible that an iid guarantee might be sufficient to at least solve the random unacceptability problem.

However, getting an iid guarantee in the first place might be quite difficult, as it would seem to require there being absolutely no detectable differences between the training and deployment distributions. This is especially difficult if the model is actively looking for differences between the training and deployment distributions, as would happen in the next hard case.

**Conditional defection.** Suppose you have a [deceptive](https://www.alignmentforum.org/posts/zthDPAjh9w6Ytbeks/deceptive-alignment) model—that is, one which is trying to appear aligned during training, but actually wants to do something else during deployment.[^11] Then, it's going to be searching for ways to tell whether it's in training or not such that it might be quite difficult for an adversary to actually find any inputs on which it's unacceptable. [Paul provides the example](https://ai-alignment.com/training-robust-corrigibility-ce0e0a3b9b4d) that one possible check the model could perform might be to look for a factorization of [RSA-2048](https://en.wikipedia.org/wiki/RSA_numbers#RSA-2048) in its input. RSA-2048 is a large semiprime number that was featured as part of the [RSA Factoring Challenge](https://en.wikipedia.org/wiki/RSA_Factoring_Challenge). Though no factorization of RSA-2048 is currently known, it is likely that at some point someone will publish such a factorization. Thus, by only behaving unacceptably when it sees a factorization of RSA-2048, a deceptive model can all but guarantee that adversarial training will never be able to produce an input on which it behaves unacceptably—since that would require factoring the number—but that will still be fairly likely to eventually occur during deployment.

[^11]: Why you would ever actually get a model of this form is a complicated question; for a complete treatment, see the section on deceptive alignment in “[Risks from Learned Optimization](https://arxiv.org/abs/1906.01820).”

The RSA-2048 example generalizes to a large family of cases wherein a deceptive model is conditioning its unacceptable behavior on some predicate $\alpha$ such that it is easier to check whether $\alpha(x)$ holds for some $x$ than it is to generate an $x$ for which $\alpha(x)$ holds. In the RSA-2048 case,
$$
    \alpha(x) = \text{factorization of RSA-2048} \in x.
$$
However, there are many other possible concerning $\alpha$. For example, if the training data includes lots of web text, one simple variable which is likely to be highly correlated with whether the model is in training or not is the date. Thus, one possible $\alpha$ might be $\alpha(x) = \text{year}(x) == 2030$. Another possibility might be to choose an $\alpha$ for which it is not currently known whether there exists any $x$ which satisfies it. This could be a problem in any situation where $\text{Adv}$ is required to definitively demonstrate that $\exists x \in X,~ \alpha(x)$. For example, consider $\alpha(x) = \text{proof of the Riemann Hypothesis} \in x$. In the RSA-2048 example, $\text{Adv}$ can prove that there is some string that contains a factorization of RSA-2048 (since it is known that RSA-2048 is not prime), but in this example, that is no longer possible.

Furthermore, even in the situation where a deceptive model cannot detect any differences between the training and deployment distributions, it may still attempt to randomly defect some proportion of the time in the hope that its defection occurs during deployment. However, if it can be enforced that samples from the model during training and deployment are in fact iid, then you can still get an average case acceptability guarantee as above. Interestingly, if we take the model from above and assume that $M$ gets unit utility for defecting at some point during deployment and zero utility otherwise we can find $M$'s optimal per-step cooperation probability and use that to determine the overall probability of unacceptable behavior during deployment if we end up with such a model. In particular, in the case where our training process can only deal with conditional defection, but always produces a model pursuing random defection, we get a probability of unacceptable behavior of
$$
    \mathbb P(\exists x \in \mathbb X_\text{deploy},~ C(M, x)) = \frac{m}{m + n}
$$
which is precisely the result derived from using a maximum likelihood estimate in the random defection case rather than a uniform Bayesian prior.

Another interesting possible phenomenon that could arise in the deceptive case is that some inputs might be inherently more important to the model such that it is more likely to defect on those inputs than others. If the model's notion of which inputs are most important to defect on matches up with those inputs where defection is likely to be most problematic, then that could be another way for the situation to be worse than the above guarantee even in the iid case.[^12]

[^12]: In particular, it might be that $C(M, x)$ is iid relative to $x \sim \text{deploy}$, but still becomes more likely when conditioning on $x$ being important to us.

**Meta-learning.** “[Risks from Learned Optimization](https://arxiv.org/abs/1906.01820)” suggests that the case where inner alignment is most concerning is the case involving a model that is itself implementing some sort of search or learning process. Primarily, we have been assuming that the problem with this situation is the objective by which this search is being performed, and that if that objective can be aligned with the loss function, then we are satisfied. However, this is not in general the case, as even if a model's objective is aligned, its search process might not be. Conceptually, we can think of this problem as the problem of “forwarding” the safety guarantee we have about the training process to the meta-learning process.

[My counterexample to the safety of minimal circuits](https://www.alignmentforum.org/posts/fM5ZWGDbnjb7ThNKJ/are-minimal-circuits-deceptive) is a theoretical example of what a failure of this form might look like. Alternatively, as a more concrete example, consider a model which has learned to do some form of meta-learning such that it is implementing its own expected risk minimization procedure. In this case, even if we have a strong guarantee that our model isn't going to be deceiving us, we might not have the same guarantee about whatever policy results from the model's meta-learning. Furthermore, performing search in a particular way could be a form of defection: a deceptive model could choose to perform a policy search that is more likely to produce models aligned with it than it is to produce models aligned with the actual loss function.

**Suboptimality alignment.** One concerning form of misalignment discussed in “[Risks from Learned Optimization](https://arxiv.org/abs/1906.01820)” is that of suboptimality alignment, wherein the model appears aligned on the training distribution due to some sort of defect or reasoning failure. For example, it might be that a model is currently non-deceptive, but if given more time to think about the best strategy for it to implement, or more information about its current situation, it would become deceptive. This is a particularly concerning case because it implies that not only must the overseer verify that there is no unacceptable behavior currently happening in the model, it must also verify that there will continue to be no unacceptable behavior regardless of the possible situations that the model could find itself in during deployment. Furthermore, if the environment contains adversaries (other AI systems, for example) that can specifically identify those situations in which the model will behave deceptively, this sort of failure mode could be quite difficult to avoid.

**Acceptability modeling.** Another interesting hard case is that of a model which is itself implementing some unacceptability predicate $C^-$ to guide its behavior. In this situation, the overseer must look for any deviation between $C$ and $C^-$ to verify the model. One thing which is likely to be particularly helpful in this situation is if the overseer has access to the history of the model so that it can see how $C^-$ has been trained and verify that it wasn't purposefully constructed to deceive the overseer. One particularly concerning scenario might be if the model is using $C^-$ as a tool for determining when to defect, defecting only when it predicts the overseer won't see its defection as unacceptable.

&nbsp;

## Conditions for success

In light of the above hard cases, we can attempt to establish those conditions that seem necessary for us to get a strong acceptability guarantee out of our framework as presented previously. First, we can factor the problem of getting the above framework to work into two broad subproblems:

1. **The recursion problem:** how do you prevent $\text{Amp}(M)$ from behaving unacceptably if $M$ is behaving unacceptably?
2. **The oversight problem:** even assuming $\text{Amp}(M)$ is acceptable, how can it oversee an unacceptable $M$ into becoming acceptable?

The fact that these two subproblems come apart here is due to one of the core trickeries we are relying on with this approach: we are asking the model to be able to oversee itself. In particular, since $C(M, x),~ P_M,~ \text{and Adv}$ are all implemented by calling $\text{Amp}(M)$, it has to be the case that, for a misaligned $M$, not only can $\text{Amp}(M)$ detect that misalignment, but also it shouldn't itself be misaligned.

While the recursion problem is very similar for all the different components of the system, the oversight problem can be split into a number of distinct subproblems:

1. if $P_M$ thinks the probability of unacceptable behavior during deployment is less than $\epsilon$, then the probability of unacceptable behavior during deployment is actually less than $\epsilon$,
2. if $M_\text{bad}$ has probability of producing unacceptable behavior during deployment greater than $\epsilon$, then there exists some $\alpha \in \mathbb X_\text{pseudo}$ that will convince $P_{M_\text{bad}}$ of that fact,
3. it is not that hard for $\text{Adv}$ to find such an $\alpha$, and
4. there exists a model $M_\text{good}$ that is not that hard to find such that $P_{M_\text{good}}$ is confident that the probability of $M_\text{good}$ producing unacceptable behavior during deployment is less than $\epsilon$.

I will start by addressing the recursion problem, then move on to each of the above per-condition oversight problems.

**The recursion problem.** First, we're going to need to rely heavily on the details of $\text{Amp}$ to make this work. Having humans in the loop as part of $\text{Amp}$—at least at the beginning—seems likely to be critical, for example, to ensure that $\text{Amp}(M)$ is more aligned and more capable than $M$. Second, the recursion doesn't actually have to work for all $M \in \mathbb M$—rather, we only need our acceptability guarantee to hold along any path through model space that could actually be traversed by our training procedure.

Thus, it's fine if our procedure fails if given a sufficiently unacceptable model, as long as our procedure can prevent such models from ever arising. For example, if we always used an old version of $M$ that we were confident in for implementing $\text{Amp}(M)$, then we would just need it to be the case that $M$ couldn't get to the point where it would be able to deceive $\text{Amp}(M_\text{old})$ in-between oversight. As a concrete implementation, imagine some sequence of $M_i$ and suppose the minimum number of steps for oversight to start failing is $r$.[^13] Then, at step $i+r-1$ we can implement oversight by calling $\text{Amp}(M_i)$ to binary search on $M_{i+1},~ M_{i+2},~ \ldots,~ M_{i+r-1}$ looking for any point at which unacceptable behavior is introduced and then retrain from right before that point in such a way that fixes the unacceptability.

[^13]: Note that $r$ here is not the minimum number of steps before $M_{i+r}$ can become unacceptable, but rather the minimum number of steps before $M_{i+r}$ can deceive $\text{Amp}(M_i)$ into thinking it's acceptable when it's not.

If we use an implementation of this form, then the difficulty of the recursion problem is likely to depend heavily on the difficulty of the oversight problem: the fewer asks we need to make of $\text{Amp}(M)$ to produce good oversight, and the better our oversight is at detecting problems, the more leeway we have. Thus, though I will primarily be addressing the oversight problem, I anticipate that all of my discussion of the oversight problem will also be highly relevant to the recursion problem.

**If $P_M$ thinks the probability of unacceptable behavior during deployment is less than $\epsilon$, then the probability of unacceptable behavior during deployment must actually be less than $\epsilon$.** There are two major components to this condition: $P_M$ must have a good model of unacceptable behavior and $P_M$ must be well-calibrated over whether some model $M$ will produce output which is unacceptable according to that model during deployment. For the first condition, if we assume that acceptability is a bright enough line that we can train a model to clearly distinguish between acceptable and unacceptable actions, then we can satisfy that condition. The second condition, however—of $P_M$ actually being well-calibrated—is somewhat more complicated. Specifically, we need $P_M$ to be well-calibrated over questions of the form $P_M(\alpha(x)\ |\ x \sim \text{deploy})$ and $P_M(C(M, x)\ |\ \alpha(x),~ x \sim \text{deploy})$, since those are the questions we're going to be asking it.

First, $P_M$ has to be well-calibrated over $x \sim \text{deploy}$. In particular, this requires $P_M$ to have a good model of the deployment distribution. This seems tough—and possibly problematic if it also requires $M$ to know more about the differences in distributions such that it can more effectively choose when to defect—though in fact it's not quite as bad as it might seem: it's fine if $P_M$ is fairly uncertain about most $\alpha$—it just can't be so uncertain that it becomes impossible to ever reduce the combined probability below $P_M$'s prior on $C(M, x)\ |\ x \sim \text{deploy}$.

Second, $P_M$ has to be well-calibrated over $x\ |\ \alpha(x),~ x \sim \text{deploy}$. This is even more difficult because $P_M$ cannot actually sample at all from that distribution, as $\alpha(x)$ could require something like a factorization of RSA-2048. However, there are some reasons to believe that this might still be tractable. First, $P_M$ doesn't have to answer arbitrary questions about this distribution—only the probability of $C(M, x)$. And if we assume that a predicate that $M$ has no knowledge of or way of testing won't affect the probability of $C(M, x)$, then that means that $P_M$ only has to care about those $\alpha$ which actually matter to $M$. Furthermore, since $P_M$ is an amplified version of $M$, it should know about all those $\alpha$ which $M$ knows about, and thus should have a real shot at being able to answer questions conditional on $\alpha$.

**If $M_\text{bad}$ has probability of producing unacceptable behavior during deployment greater than $\epsilon$, then there must exist some $\alpha \in \mathbb X_\text{pseudo}$ that will convince $P_M$ of that fact.** Since our procedure can handle arbitrary $\alpha$, we can make $\mathbb X_\text{pseudo}$ large enough to contain whatever $\alpha$ we might need. Thus, the hard part of this condition is convincing $P_M$. Assuming away the recursion problem such that $P_M$ is trying to do the right thing, it still needs to be the case that $M_\text{bad}$ has no way of tricking $P_M$ into believing that it's acceptable when it in fact isn't. This condition is likely to depend heavily on how good $P_M$'s transparency tools are, and in particular how robust they are to attempted deception on behalf of $M_\text{bad}$.

Importantly, however, $P_M$ doesn't have to be confident that $M_\text{bad}$ is unacceptable—it just has to be the case that $M_\text{bad}$ can't convince $P_M$ to be confident that it is acceptable. Thus, since $P_M$ should be highly uncertain by default—and should stay that way unless the model is highly transparent—this condition should not be too difficult to satisfy. In particular, it needs it to be the case that Amp(M) is only convinced that a pseudo-input is fine if M is sufficiently transparent such that Amp(M) knows it would be able to detect any unacceptable behavior if it existed.

**It must not be that hard for $\text{Adv}$ to find such an $\alpha$.** In his original formulation, [Paul noted](https://ai-alignment.com/training-robust-corrigibility-ce0e0a3b9b4d) that the “most fundamental obstruction is implementing a good adversary.” In this formulation, however, much of the difficulty has been transferred from the adversary to the probability model. For example, under this model it is fine to include an $\alpha$ that is just “an input such that $M$ is unacceptable,” in which case the entirety of the work falls to $P_M$. The work still has to happen somewhere, however: either $\alpha$ needs to encode lots of relevant information for $P_M$, or $P_M$ has to be able to discover that information on its own.

Thus, let's suppose that most of the relevant work is happening in $\text{Adv}$. In that case, we need $\text{Adv}$ to be able to figure out when $M$ is likely to behave unacceptably. As with the previous condition, this is likely to depend heavily on how transparent $M$ can make itself: there has to be some level of transparency enforceable by $\text{Adv}$ such that only good $M$ can pass without letting $\text{Adv}$ produce an $\alpha$ that convinces $P_M$. Importantly, however—as with the previous condition—since $P_M$ is uncertain by default, $\alpha$ doesn't have to be that convincing: it only has to be good enough to convince $P_M$ that there is non-negligible chance of unacceptability. Thus, the key condition here is that any unacceptable model must have some at least moderately plausible failure mode which is not that hard to find. Then, for opaque models, $\text{Adv}$ can do this by coming up with something that isn't ruled out by the transparent portions, and for transparent models, it should be able to directly determine any failure modes.

**There must exist a model $M_\text{good}$ that is not that hard to find such that $P_M$ is confident that the probability of $M_\text{good}$ producing unacceptable behavior during deployment is less than $\epsilon$.** First, note that the first condition gives us that $M_\text{good}$ is actually good if $P_M$ thinks it is. Thus, this condition is saying that it must not be that hard to find an acceptable $M_\text{good}$ such that $P_M$ can actually verify $M_\text{good}$'s acceptability. If we assume that it is not that hard to produce only acceptable actions—that doing so doesn't interfere much with performance and that an action's acceptability is not that hard a condition to detect—then there should exist some acceptable $M_\text{good}$ which is not that hard to find.

The hard part, however, is that there has to exist a not-that-hard-to-find $M_\text{good}$ which is not just acceptable but also _verifiably_ acceptably. Not only does $M_\text{good}$ have to be acceptable and not that hard to find, it has to actually have some way of convincing $\text{Amp}(M)$ of that fact. This is likely to depend heavily on how transparent $M_\text{good}$ can make itself to $P_M$, since if we are assuming that $M_\text{good}$ is acceptable then it should actually be trying to make itself transparent, which should help. However, whether its acceptability can be easily verified up to a high degree of certainty by $P_M$ is going to depend on the degree to which it can actually succeed at that task. Since this condition actually requires $P_M$ to achieve a high degree of certainty, it could be much more difficult than the other conditions: the default of $P_M$ always defaulting to its prior and being highly uncertain doesn't work here. Thus, this condition—of there actually existing a highly-transparent, competitive model—seems to be the most critical.

&nbsp;

## The core problem: transparency

A theme common to many of the conditions for success given above—especially the last, hardest condition—is transparency. If $M_\text{good}$ can make itself transparent enough that $\text{Amp}(M)$ can verify its acceptability in such a way that doesn't make $M_\text{good}$ too much harder to find or hurt its performance too much, then—with a few caveats—the above proposal should mostly go through. Alternatively, if no such transparency method exists, then the above approach—at least as presented here—seems to have little chance of working. Thus, we can frame the work presented here as a way of elucidating exactly what sorts of transparency techniques are likely to be necessary to solve the overall alignment problem. In particular, we would like to be able to reduce the burden on transparency by figuring out what the easiest possible transparency techniques are that would fully solve the problem.

One possible starting point for tackling this question of what sorts of transparency techniques are likely to be necessary is Paul's notion of [ascription universality](https://ai-alignment.com/towards-formalizing-universality-409ab893a456). Ascription universality gives us a way of talking about when we should trust a system, as well as when we should trust one more than another. Specifically, we want it to be the case that $\text{Amp}(M)$ epistemically dominates $M$ such that, regardless of any information we get about the beliefs of either $M$ or $\text{Amp}(M)$, we will always trust $\text{Amp}(M)$'s predictions about all quantities better than our own. This condition is somewhat too strong, however, as we don't need to trust $\text{Amp}(M)$ on all questions, only those relevant to the oversight process. Those questions which are relevant to the oversight process, however, have the property of primarily being questions about the internal structure of $M$, which makes the condition of $\text{Amp}(M)$ knowing strictly more than $M$ about them somewhat difficult to satisfy. Thus, the critical transparency condition that this model suggests we need is for $\text{Amp}(M)$ to know more about $M$ than $M$ does.

Unfortunately, epistemic dominance is a statement about a model's expectations rather than its internal structure, which means it doesn't give us a very mechanistic understanding of what a model which satisfies such a condition might look like.[^14] However, we can still think about the sorts of transparency tools which might enable us to get to the point where we could verify such a condition. In particular, $\text{Amp}(M)$ is going to need some way of fully understanding $M$. We can isolate three distinct ways in which that can be done:

[^14]: Though no more mechanistic approach currently exists, I am excited about [future research](https://www.alignmentforum.org/posts/Zj2PgP5A8vY2G3gYw/optimization-provenance) possibly yielding progress in this domain.

1. **Transparency via inspection:** use transparency tools to understand $M$ via [inspecting the trained model](https://distill.pub/2018/building-blocks/).
2. **Transparency via training:** incentivize $M$ to be as transparent as possible as part of the training process.
3. **Transparency via architecture:** structure $M$'s architecture such that it is inherently more transparent.

Though it is currently unclear which of these approaches is likely to be the most fruitful, it seems likely that some combination of all of them will be necessary. Whatever approach we take, however, one of the major conditions will be for it to scale well to larger, more complicated models so that this whole approach can stay competitive.

Specifically, some of the sorts of transparency guarantees that are likely to be useful in this domain might include:
- The ability to access $M$'s model of the world: that is, what facts about the world does $M$ know that are going into producing its output? In particular, what implicit knowledge is $M$ using that isn't represented in its explicit output?
- Knowledge of what factors most highly impact $M$'s decisions. In particular, if there is some condition $\alpha$ such that $M$ only behaves acceptably if $\alpha$ is true, then we want to be able to know that $M$'s output is highly dependent on $\alpha$.
- Good understanding of $M$'s counterfactual behavior. In particular, we want to be able to know broadly what $M$ will do in situations (such as RSA-2048) where we can't explicitly instantiate an input which can be fed to $M$ directly.
- The ability to access $M$'s objective: that is, if $M$ is running some search process, what is that search process optimizing for? If $M$ is searching over possible strategies which it is considering implementing, what criterion is it using to select among them?

Included below are two examples of possible ideas for how a full transparency scheme might work using some of the above tools.

**Transparency for agent objectives.** First, suppose we assume the conjecture that [models implementing highly coherent optimization processes are the most competitive](https://www.alignmentforum.org/s/r9tYkB2a8Fp4DN8yB/p/q2rCMHNXazALgQpGH). If this conjecture is true, it should be possible to coherently separate such a model into pieces representing the different components of its optimization process such as its world model, optimization procedure, and objective.

Inspection, training, and architectural transparency methods could be combined to achieve such a separation. First, architectural transparency could be used to structure the model to have pieces corresponding to the different components of its optimization process—e.g. a separate world model piece and optimization procedure piece. Second, inspection transparency could be used to verify that the whole world model was just in the world model piece and not in other parts of the model as well—and similarly for the other components such as the model's objective. Finally, training transparency could be used to incentivize the model to be as transparent according to the inspection transparency process as possible.

If such a scheme was able to work, then $\text{Amp}(M)$ might be able to directly verify that $M$'s objective was aligned, while for the world model and optimization procedure only having to verify that they are in fact value-neutral. Such value-neutrality verification could then, for example, be done via an impact measure such as [Attainable Utility Preservation](https://arxiv.org/abs/1902.09725) or [Relative Reachability](https://arxiv.org/abs/1806.01186) both of which are forms of measuring the degree to which an action advantages one set of values over others.

**Pure world model transparency.** Alternatively, suppose we don't accept the conjecture that you need to implement a coherent optimization process to be competitive. In this world, we have another option available to us: rather than having to ensure we get a transparent objective, we can just train a model that has no objective—that is, we can try to train a purely predictive model with only a world model but no optimization procedure or objective.

To do this, we could use architectural transparency to structure the model to be composed of only a world model portion trained in a purely generative setting and use inspection transparency to verify that it is in fact only a world model and hasn't learned any sort of optimization procedure instead. We could also again use training transparency to incentivize the model to be as transparent to the inspection process as possible.

In this situation, the training and amplification procedures become somewhat more complicated, as we still want to be able to extract actions out of something that is just a world model. To do this, we could implement $\text{Amp}(M)$ via a human with access to sufficient inspection transparency tools to enable them to make use of $M$'s world model to guide their decision-making, though the obvious concern here is whether this would actually be sufficient to stay competitive with other approaches.

Alternatively, even if we did need our model to implement some sort of optimization procedure to be competitive, extracting just the world model might still be quite good, as it could be enough to get an iid guarantee. Specifically, if we were able to understanding the model's beliefs about the differences between the training and deployment distributions, we might able to only deploy the model in situations where we know it can't tell it's being deployed, hopefully giving us a good iid guarantee. See “Make use of $M$'s $x \sim \text{train}$ model” under “Other approaches” for a further treatment of this possibility.

Finally, a model's world model seems to be one of the easiest pieces to extract, as it can naturally be identified by looking for the portions of $M$ with the greatest mutual information with the world. Thus, one good first step for making either of the above transparency schemes go through—since both of them involve world-model extraction—might be to gain a better understanding of what transparent world models look like and how they can be extracted.[^15]

[^15]: Much research in the direction of extracting interpretable world models already exists—such as Carter et al.'s [Activation Atlases](https://distill.pub/2019/activation-atlas/), for example—though it is currently unclear to what extent such techniques will scale to more powerful AI systems.

&nbsp;

## Other approaches

This section is not meant to be a complete list of possible alternative strategies to solving this problem, but rather an analysis of some other promising directions that were looked into as part of the research that went into this post.

**Call $P_M(C(M, x)\ |\ x \sim \text{deploy})$ directly.** As I noted previously, one possible $\alpha$ could simply be $\alpha(x) = C(M, x)$, in which case $L_M$ simply reduces to
$$
    L_M = P_M(C(M, x)\ |\ x \sim \text{deploy}).
$$
Thus, a reasonable question to ask is whether we should simply use this as our acceptability penalty directly—that is, how much do we gain from having an adversary? There are two reasons we might want to actually have an adversary.

First, the use of an adversary might allow us to inject additional useful information into the system. Specifically, we are giving the system the following information: the fact that it should be using an adversarial training setup, and the specific pseudo-input set $\mathbb X_\text{pseudo}$ that it should be considering. In particular, our ability to specify $\mathbb X_\text{pseudo}$ gives us the ability to constrain the adversary such that it is forced to confine its demonstration into some structure that enables it to be easily checked by $P_M$. In practice, however, we might want to implement this simply by letting amplification decompose the original question into the adversarial setting itself, but even in that case it's still worth analyzing why or why not amplification might want to adopt that particular decomposition.

Second, the decomposition into adversary and overseer might significantly aid training as it allows us to train the adversary on the reward signal of maximizing $P_M(C(M, x)\ |\ \alpha(x),~ x \sim \text{deploy})$ rather than just relying on the reward signal from amplification. Furthermore, if we're not using a standard amplification setup as in the pure world model transparency case described previously, then we might need this additional training signal as we wouldn't necessarily get it for free out of decompositions anymore in that regime.

**Implement the adversary as a separate system.** Another way in which the use of an adversary could be made to significantly improve upon just calling $P_M(C(M, x)\ |\ x \sim \text{deploy})$ directly is to have the adversary implemented as a separate system. One major problem with such a setup, however, is that we then need another system for guaranteeing the acceptability of the adversary. If we restrict the adversary's task sufficiently such that its input data isn't rich enough for it to learn complex deceptive behavior, however, then producing such an acceptability guarantee might be sufficiently easier than the original problem that it provides an actual reduction. For example, we could train $\text{Adv}$ to solely be a theorem prover that produces proofs of the form $\alpha \to \exists x \in \mathbb X,~ C(M, x)$ where we incentivize $\text{Adv}$ to select its assumptions $\alpha$ to maximize $P_M(\alpha)$.

**Make use of $M$'s $x \sim \text{train}$ model.** One assumption we are relying on in this setup is that $P_M$ have a model of $x \sim \text{deploy}$. It is interesting to explore what else one can do with other versions of that assumption. In particular, if one assumes that $\text{Amp}(M)$ can access $M$'s model of $x \sim \text{deploy}$ and $x \sim \text{train}$, then it might be possible to turn that into an iid guarantee. One simple way of doing this might be to only deploy $M$ in situations where $x$ has high probability according to $M$'s model of $x \sim \text{train}$. Alternatively, such a condition could even be integrated into the training process if $M$ is trained to match its model of $x \sim \text{deploy}$ to its model of $x \sim \text{train}$ such that it is trained to “forget” about any distributional shift it might otherwise know about. Importantly, however, approaches of this form can only produce an iid guarantee, which must be combined with some analysis of the form presented previously to turn it into an acceptability guarantee.

**Ensemble over many $M$.** Another approach which is not explored in this post is the use of ensembling to improve acceptability. If ensemble consensus is required to produce an output, then as long as there is some $M_\text{good}$ in the ensemble, its outputs should always be guaranteed to be acceptable. Thus, ensembling can reduce the burden on us having to produce precisely $M_\text{good}$ in exchange for the cost of spending additional compute training additional $M$. Importantly, however, this only works if the different $M$ are sufficiently distinct that the probability of any one of them being good is relatively independent from the probability of the others being good, which might be a difficult condition to satisfy in practice. Furthermore, ensembling is less a solution in and of itself and more of a strategy we can use to improve upon other acceptability guarantees, as we still need to actually have some argument for why we will be likely enough to find $M_\text{good}$ in the first place that ensembling can get us the rest of the way there.

&nbsp;

## Conclusion

Though this post goes most in-depth into the particular proposal of relaxed adversarial training, it is my hope that many of the ideas that have been discussed here will be broadly useful for advancing our understanding of different possible approaches to solving inner alignment in general. In particular, I believe that one of the best ways in which we can get traction now on how to solve hard AGI alignment problems such as the ones discussed here is to analyze concrete schemes and hard cases so that we can get an idea now of what sorts of problems we're likely to encounter in the future on the road to AGI.

To that end, I believe that one of the most important takeaways we can draw from the analysis presented here, regardless of what sort of approach we actually end up using, is the central importance of transparency. Without being able to look inside our model to a significant degree, it is likely going to be very difficult to get any sort of meaningful acceptability guarantees. Even if we are only shooting for an iid guarantee, rather than a worst-case guarantee, we are still going to need some way of looking inside our model to verify that it doesn't fall into any of the other hard cases. One of the ways in which this sort of work can be most helpful, therefore, is in providing research directions for transparency: what is it that we actually need to get out of transparency to be able to produce a good acceptability guarantee?

This work suggests, for example, that one of the critical condition that we need is for our transparency scheme to be good enough such that there actually exists some model that can demonstrate to an overseer that it is acceptable. Thus, we need to answer the question of what would be sufficient to convince us (or at least an amplified version of us) that a model is acceptable. One possible first step towards something of this form might be working on world model extraction as described previously, though significant future work—likely involving major advances regarding our understanding of interpretable world models—still seems necessary to make anything of that form go through.
