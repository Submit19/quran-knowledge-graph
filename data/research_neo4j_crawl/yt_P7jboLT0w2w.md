# Transcript: https://www.youtube.com/watch?v=P7jboLT0w2w

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 623

---

**[00:09]** Yes. So, hi everyone. Uh, I am Ashetta  
**[00:12]** from AWS and today I'll be going through  
**[00:16]** a developer journey of building smarter  
**[00:19]** applications.  
**[00:22]** Well, and the journey begins on a Friday  
**[00:24]** movie night when I and my friends start  
**[00:28]** having a healthy discussion on what  
**[00:30]** movie we should watch together.  
**[00:34]** So, the criteria for me is pretty  
**[00:37]** simple. The movie should not ex uh  
**[00:40]** exceed 150 minutes. Anything above 2 and  
**[00:44]** a half hours and I'm done.  
**[00:47]** Now, my friend Rahul, he's a total  
**[00:50]** sci-fi thriller. a sci-fi and thriller  
**[00:52]** fan and he does not like any other genre  
**[00:56]** except these two. On the other hand, my  
**[01:00]** friend Rabi has a long list of  
**[01:02]** requirements. He's a big fan of the  
**[01:04]** Nolan's entourage and loves Inception,  
**[01:08]** The Dark Knight, and Interstellar. And  
**[01:11]** he wants at least a familiar face from  
**[01:15]** these three movies in the movie that  
**[01:17]** he's going to watch.  
**[01:19]** And not only that, he only wants  
**[01:22]** seasoned directors who have directed at  
**[01:26]** least three movies.  
**[01:30]** So what do I do?  
**[01:32]** I am a developer and whenever we  
**[01:36]** developer face issues, we build  
**[01:39]** applications.  
**[01:40]** And this time let us build an agentic  
**[01:43]** application to solve this always  
**[01:47]** occurring problem of deciding which  
**[01:49]** movie we should watch.  
**[01:52]** But before we write any piece of code, I  
**[01:56]** want to make sure that all of us are on  
**[01:58]** the same page about what an agentic app  
**[02:02]** actually means.  
**[02:05]** So let us look at what  
**[02:08]** we've been building so far. So  
**[02:11]** traditional apps are apps where the user  
**[02:14]** does something and the app responds. So  
**[02:18]** it's basically you tap a button and you  
**[02:20]** get a result. Thus this traditional app  
**[02:24]** does not think. It just reacts. And  
**[02:27]** every app that we have built or used say  
**[02:30]** over the past decade works like this.  
**[02:36]** But now we have agentic apps. This is  
**[02:40]** different. What happens here is that the  
**[02:43]** user says something and the agent starts  
**[02:47]** a loop. It reasons about what it just  
**[02:51]** heard and then it goes on to do  
**[02:54]** something like it can just pick a tool.  
**[02:57]** It can say decide on a database query  
**[03:01]** and say decide to do an API call and  
**[03:04]** then simply runs the tool.  
**[03:08]** It then looks at what came back. And  
**[03:11]** here's the part that matters. You can  
**[03:13]** see the curved arrow on the screen. So  
**[03:16]** if the result isn't good enough, it goes  
**[03:20]** back to the reasoning step and tries  
**[03:23]** something else. You know, maybe it is  
**[03:25]** going to rewrite the query, maybe it is  
**[03:27]** going to try picking up a different tool  
**[03:30]** altogether.  
**[03:34]** And the loop that I just showed you, the  
**[03:36]** reason, act, observe, and repeat. Let us  
**[03:40]** now zoom in on it a little more to  
**[03:43]** understand how it actually works. You  
**[03:46]** know, like what goes into the agent and  
**[03:50]** what is it that comes out.  
**[03:53]** So on the left hand side you can see  
**[03:56]** three inputs  
**[03:58]** and the agent will need all of these  
**[04:01]** three inputs to get started.  
**[04:05]** So first we have the goals or the  
**[04:08]** instructions.  
**[04:09]** Now this is us telling the agent what it  
**[04:13]** needs to do. So it can be things like  
**[04:16]** help me find a movie for my Friday night  
**[04:19]** or say book me a flight to Amsterdam or  
**[04:23]** it can be say register me for notes AI.  
**[04:27]** So the agent needs to know what it is  
**[04:30]** actually working towards.  
**[04:34]** Then we have tools and their  
**[04:36]** descriptions.  
**[04:38]** So this is how the agent actually gets  
**[04:41]** hands. So you give it a list of things  
**[04:44]** it can do. Now that can be as simple as  
**[04:48]** quering a database, calling an API,  
**[04:52]** being able to do web search, or even say  
**[04:55]** just send an email.  
**[04:58]** And then what you do is you describe  
**[05:00]** each of these in simple plain English.  
**[05:04]** And what your agent is going to do is  
**[05:07]** that the agent will read those  
**[05:09]** descriptions  
**[05:11]** and pick up the right tool for the  
**[05:14]** situation.  
**[05:16]** So think of it like handing someone a  
**[05:19]** toolbox and a manual. So they are able  
**[05:22]** to look at the manual say figure out  
**[05:25]** which wrench fits and simply grab it.  
**[05:30]** Then the third thing is context  
**[05:33]** and this is everything your agent  
**[05:35]** already knows. So all your conversations  
**[05:40]** uh that you've had with the agent, all  
**[05:43]** your user interactions,  
**[05:45]** any relevant documents,  
**[05:49]** whatever the agent already knows is part  
**[05:52]** of context and this is basically like  
**[05:54]** your background information. So what  
**[05:57]** happens is without context the agent is  
**[06:00]** going to scratch start from scratch  
**[06:03]** every single time but with context it  
**[06:07]** remembers and context you can say it's  
**[06:10]** your agent's memory and the knowledge  
**[06:11]** base.  
**[06:14]** Now what happens is all these three the  
**[06:17]** goals instructions tools and their  
**[06:20]** description and the context go to the  
**[06:23]** agent  
**[06:24]** and at the core we have the brain. Now  
**[06:28]** the brain here is our large language  
**[06:31]** model. Now it can be anything. It can be  
**[06:34]** your claude, it can be your llama, it  
**[06:36]** can be your nova. Whatever you decide to  
**[06:38]** choose.  
**[06:40]** The agent is then going to package up  
**[06:43]** the goal, the tools and their  
**[06:45]** descriptions and the context into a  
**[06:50]** single prompt and it sends it to the  
**[06:54]** LLM.  
**[06:56]** And what is this prompt? So this prompt  
**[06:58]** is basically saying here's what I need  
**[07:01]** to do. Here is what I can use. Here is  
**[07:06]** what I know so far. what should I do  
**[07:09]** next?  
**[07:10]** So, our LLM is now going to reason  
**[07:14]** through all of that and come back with a  
**[07:17]** decision.  
**[07:18]** It'll be either I want to call this tool  
**[07:21]** with these arguments or say I have  
**[07:23]** enough information and here's my answer.  
**[07:26]** Now in case it is a tool call the agent  
**[07:29]** is going to take an action which means  
**[07:32]** it will do something which can be like  
**[07:35]** calling an API, quering a database,  
**[07:38]** running a calculation, any of these and  
**[07:43]** all these actions will happen in an  
**[07:45]** environment.  
**[07:46]** Now that environment can be your  
**[07:48]** computer, it can be your cloud service,  
**[07:51]** it can be your AWS console, it can be  
**[07:53]** anywhere.  
**[07:55]** And the agent now isn't just talking  
**[07:57]** about doing something, it is actually  
**[08:00]** doing it.  
**[08:02]** And then we have our loop. So after the  
**[08:06]** action runs, the agent is going to  
**[08:09]** observe the result. Did my API call  
**[08:12]** work? What data actually came back? Was  
**[08:16]** there an error? And all these  
**[08:18]** observations are then fed back to the  
**[08:21]** agent. You can see that arrow going back  
**[08:24]** to the agent and the whole cycle starts  
**[08:29]** again. Your think, act, observe and  
**[08:33]** until the goal is done or the agent hits  
**[08:36]** a limit that you have set.  
**[08:39]** So now you could build all of this  
**[08:41]** yourself. the prompt construction, the  
**[08:44]** tool dispatch, the result parsing, the  
**[08:47]** loop management, but that's a lot of  
**[08:50]** plumbing and undifferentiated heavy  
**[08:52]** lifting. And what we're going to do next  
**[08:55]** is we are going to use a framework that  
**[08:58]** handles it for us.  
**[09:02]** So, we'll be using the strands agent  
**[09:04]** TypeScript SDK, which is an open-source  
**[09:08]** project for building AI agents in  
**[09:10]** Typescript. So you can define your  
**[09:13]** tools, point it at a model and it  
**[09:16]** handles your entire reasoning loop, the  
**[09:19]** prawn construction, your tool dispatch,  
**[09:22]** result evaluation and the decision  
**[09:25]** whether to loop again or respond  
**[09:29]** and it works with React Native which is  
**[09:32]** why we can run this agent on device.  
**[09:37]** So well uh let's start building now. So  
**[09:41]** the first attempt is using only an LLM.  
**[09:46]** So now let us look at the actual code  
**[09:48]** here. And this is actually the simplest  
**[09:51]** possible agent that you can build with  
**[09:53]** strands. So you can see we have two  
**[09:56]** imports agent and the bedrock model and  
**[10:00]** both are from the strands agent SDK.  
**[10:03]** This is the only dependency we have. And  
**[10:06]** what we're going to do next is we are  
**[10:07]** going to initialize our underlying  
**[10:10]** model.  
**[10:11]** This is the brain and we are pointing it  
**[10:14]** at claw 3.7 sonnet on Amazon bedrock  
**[10:18]** which is running in US East one. And the  
**[10:22]** client config that you see it primarily  
**[10:24]** helps the client talk to bedrock  
**[10:26]** directly. And then we're going to create  
**[10:29]** the agent which will take three things.  
**[10:32]** the model that we just created, a tools  
**[10:35]** array which is empty here because we are  
**[10:37]** not calling any tools in this attempt  
**[10:39]** and a system prompt which is you are a  
**[10:42]** movie expert answer questions about this  
**[10:45]** about movies and this is basically our  
**[10:48]** baseline. So we are going to ask our  
**[10:50]** Friday night question and see what  
**[10:53]** happens when an agent will answer.  
**[10:57]** So you can see we are providing our  
**[10:59]** query here. Find me a sci-fi or thriller  
**[11:02]** under 150 minutes from a director that  
**[11:06]** has directed at least three other movies  
**[11:09]** where one where at least one cast member  
**[11:12]** has appeared in Interstellar, The Dark  
**[11:15]** Knight or Inception.  
**[11:17]** And now you can see the response that  
**[11:20]** the agent has given. So if you closely  
**[11:23]** look the agent confidently responds and  
**[11:26]** suggests the movie Transcendence  
**[11:30]** it claims that Valley Fister is the  
**[11:33]** director with more than three films  
**[11:36]** directed.  
**[11:38]** But now if you Google or look at any of  
**[11:40]** the official data sources you will find  
**[11:44]** that Wally has just directed one movie  
**[11:48]** which is transcendence.  
**[11:50]** He is actually a cinematographer  
**[11:52]** who frequently collaborates with Nolan.  
**[11:56]** So though the LLM was pretty confident,  
**[12:00]** it messed up and gave us the wrong  
**[12:02]** answer.  
**[12:05]** And why did this happen? So what just  
**[12:08]** happened with transcendence isn't a  
**[12:11]** one-off. It's a pattern. And it comes  
**[12:13]** down to what an LLM can and cannot do  
**[12:18]** when it is working alone.  
**[12:20]** So first it has a knowledge cutff.  
**[12:23]** Everything it knows comes from training  
**[12:26]** data and that data has a date on it. If  
**[12:31]** a movie came out after that date, the  
**[12:34]** LLM will not know that it exists.  
**[12:37]** And even for movies it does know about  
**[12:41]** the details can be fuzzy. We just saw it  
**[12:45]** confuse a cinematographer with a  
**[12:47]** director.  
**[12:50]** Second, it's stuck inside its own head.  
**[12:53]** It cannot do actions. It cannot search  
**[12:56]** the web. It cannot connect to a  
**[12:58]** database. It cannot call an API. It  
**[13:02]** can't run code. and it has no  
**[13:05]** interaction with the external  
**[13:07]** environment.  
**[13:09]** So when we asked it to count how many  
**[13:12]** movies fister directed, it couldn't  
**[13:16]** actually count. It just guessed and it  
**[13:20]** guessed wrong.  
**[13:22]** Third, and this is one that really  
**[13:25]** matters for our Friday night problem, is  
**[13:28]** that it has no way to guarantee that all  
**[13:32]** the constraints that the three friends  
**[13:34]** wanted to be satisfied are true at the  
**[13:37]** same time. It does try to satisfy them,  
**[13:41]** but it is doing them from memory one at  
**[13:44]** a time, hoping they all line up. There  
**[13:48]** is no verification step and there is no  
**[13:51]** query that checks and so the takeaway  
**[13:54]** here is pretty clear that we need to  
**[13:57]** give this agent tools.  
**[14:01]** So what do we do next is we decide that  
**[14:04]** let us ground the agent with real data  
**[14:07]** so it doesn't have to work from memory  
**[14:10]** and we use rag here. So when the agent  
**[14:14]** gets a question, it searches the  
**[14:17]** embedded movie descriptions for the  
**[14:20]** closest matches and pulls back the most  
**[14:24]** similar results.  
**[14:26]** That's semantic similarity. Finding  
**[14:29]** movies that sound like what you are  
**[14:32]** asking for.  
**[14:34]** So uh the agent is going to read those  
**[14:36]** results and build its answer from real  
**[14:39]** data instead of memory. So let us look  
**[14:41]** at the code.  
**[14:44]** So you can see here the model is exactly  
**[14:48]** the same. We are still using 3.7 set.  
**[14:51]** And the only addition is that we are  
**[14:54]** importing function tool to define our  
**[14:58]** tool that we are going to use.  
**[15:01]** And this is the function tool that we  
**[15:03]** have created. We are giving it a name, a  
**[15:06]** description, an input schema and a call  
**[15:10]** back. And the call back is basically the  
**[15:13]** code that will run when the agent calls  
**[15:15]** it. And by reading the description is  
**[15:20]** how the agent decides when to call it.  
**[15:25]** Uh then uh the entire agent code where  
**[15:28]** we are bringing it all together. So  
**[15:30]** again we have the same agent  
**[15:31]** constructor. Uh we have the same system  
**[15:34]** prompt as well from our attempt one.  
**[15:37]** The only thing that has changed here is  
**[15:40]** the tools array. It was empty before and  
**[15:44]** now it has search movies. So the agent  
**[15:47]** basically sees the tool, reads its  
**[15:50]** description and decide on its own when  
**[15:53]** to use it. We are not specifying that in  
**[15:56]** the prompt.  
**[16:00]** So let us now see how it works here. So  
**[16:02]** we are asking the same question and the  
**[16:05]** agent once it gets the query it thinks  
**[16:10]** that okay I have a search tool I should  
**[16:13]** use it before I try to answer  
**[16:17]** and then the agent is distilling the  
**[16:20]** question into a search friendly string  
**[16:24]** which is like sci-fi thriller short  
**[16:26]** runtime uh director cast interstellar  
**[16:29]** dark knight inception and this is what  
**[16:31]** it thinks is important  
**[16:35]** and it is calling search movies with  
**[16:37]** this string.  
**[16:39]** And what the tool then does is that it  
**[16:41]** sends back 10 movies with the closest  
**[16:45]** matching descriptions.  
**[16:48]** And now our agent has real data to work  
**[16:50]** with. It looks through the results,  
**[16:54]** picks tenant as the best match, and  
**[16:56]** responds, "Try Tenet. It's a sci-fi  
**[16:59]** thriller by Christopher Nolan." And this  
**[17:02]** is better than our previous attempt. The  
**[17:04]** agent is now looking at real movie data  
**[17:07]** and not just guessing from training  
**[17:09]** data. Tenant actually exists. It is  
**[17:12]** actually a sci-fi thriller. Nolan  
**[17:15]** actually directed it. So far so good.  
**[17:18]** But now we start thinking is the answer  
**[17:22]** actually correct for all the constraints  
**[17:25]** that were there.  
**[17:29]** So let ush go through our constraints  
**[17:31]** one by one and see what vector search  
**[17:35]** can actually handle. So we had sci-fi or  
**[17:38]** thriller Jenner genre. The search  
**[17:42]** actually matched sci-fi and thriller in  
**[17:44]** movie descriptions and tenet does happen  
**[17:47]** to be a sci-fi thriller but the search  
**[17:50]** wasn't able to actually check an actual  
**[17:54]** Jenner tag. it found that the text  
**[17:57]** sounded right. If a movie description  
**[18:00]** mentioned that this is nothing like a  
**[18:03]** typical thriller, vector search might  
**[18:06]** still match it because the word thriller  
**[18:08]** is in there. So it's important to  
**[18:10]** understand that it is matching language,  
**[18:12]** not your metadata.  
**[18:14]** Then we had a condition of under 150  
**[18:18]** minutes. And this is where it clearly  
**[18:21]** fails because tenant is exactly 150  
**[18:24]** minutes not under 150. And vector search  
**[18:28]** has no way to know that because  
**[18:31]** embeddings don't understand numbers. You  
**[18:35]** can't do less than 150 on a vector. The  
**[18:38]** number 150 and 149 will look almost  
**[18:41]** identical in the embedding space. There  
**[18:43]** is no concept of greater than or less  
**[18:45]** than.  
**[18:47]** Then we had a condition of director with  
**[18:50]** three or more other films and Nolan has  
**[18:54]** directed plenty of movies. So this  
**[18:56]** happens to be true. But the search tool  
**[18:58]** didn't count anything. It can't look at  
**[19:01]** a director and count how many directed  
**[19:04]** relationships they have. It just  
**[19:06]** returned movies that were textually  
**[19:08]** similar to the search query. and Nolan's  
**[19:11]** movie showed up because the query  
**[19:13]** mentioned Interstellar, Dark Knight and  
**[19:16]** Inception  
**[19:18]** and similarly it is matching all the  
**[19:21]** movie titles as word not with your uh  
**[19:24]** cast overlap and trying to find the  
**[19:26]** acted in relationships.  
**[19:30]** So vector search will find movie that  
**[19:33]** sound like what you want but sounds like  
**[19:36]** and what you want can be very different  
**[19:39]** things and we need something that  
**[19:41]** understands structure something that can  
**[19:43]** count relationship you know filter  
**[19:46]** numbers traverse connections and that's  
**[19:48]** where we'll move next.  
**[19:51]** So let us look at the question one more  
**[19:53]** time before we move on. This is like any  
**[19:56]** uh normal question someone would ask but  
**[19:59]** there are three things that are hiding  
**[20:01]** in it that make it really hard for an  
**[20:04]** LLM or a vector search to answer. So  
**[20:07]** first is multihop, second is  
**[20:09]** relationship aware and third is  
**[20:11]** constraint rich and let us look at them  
**[20:14]** one by one. So this is basically our raw  
**[20:17]** data uh with the movie title, director,  
**[20:21]** your actors etc.  
**[20:24]** And when I ask it this question, what  
**[20:28]** genre is the dark knight rises? You can  
**[20:31]** see it's a single hop from your movie  
**[20:34]** title to the genre's column. And this is  
**[20:37]** something any database can handle.  
**[20:40]** Now say we move to another scenario  
**[20:43]** where I ask which other movies has the  
**[20:45]** director of the Dark Knights Rises  
**[20:47]** directed and you have two hops here. one  
**[20:51]** from movie to the director and second  
**[20:54]** director to the movie.  
**[20:57]** Similarly, if we ask another question  
**[20:59]** where we try to find where a cast member  
**[21:01]** of the Dark Knight Rises has worked with  
**[21:03]** Steven Spielberg, we have three hops  
**[21:06]** here. Movie to cast to their other  
**[21:09]** movies and then back to the director.  
**[21:11]** Now you can see how difficult it is for  
**[21:15]** a normal flat table to answer correctly.  
**[21:20]** Now let's move to relationship aware. So  
**[21:23]** this is where it recognizes the type of  
**[21:26]** relationship between data points. So  
**[21:29]** even the hop that we did earlier had  
**[21:31]** some relationship. So both multihop and  
**[21:34]** relationship aware move hand in hand.  
**[21:38]** And then the third criteria that we have  
**[21:41]** is around constraint rich. What this  
**[21:44]** means is that the query will have  
**[21:46]** multiple conditions and all of them must  
**[21:50]** be satisfied simultaneously.  
**[21:53]** As you can see like these are the five  
**[21:54]** conditions that we had for our use case  
**[21:57]** like the genre the runtime the director  
**[21:59]** should have directed more than three  
**[22:01]** movies. There should be at least one  
**[22:03]** shared cast member who has appeared in  
**[22:05]** these three movies.  
**[22:08]** So when we combine all these three  
**[22:11]** characteristics, multihop traversal,  
**[22:13]** relationship awareness and multiple  
**[22:15]** constraints,  
**[22:16]** we get queries that are easy for us as  
**[22:19]** humans to write but brutally hard for  
**[22:22]** normal systems to answer. And this is  
**[22:25]** where we need something that can answer  
**[22:28]** these things and that something is a  
**[22:30]** knowledge graph. So a knowledge graph is  
**[22:32]** basically a graph where your nodes and  
**[22:35]** edges represent real world knowledge  
**[22:38]** with semantic meaning. And the nodes  
**[22:40]** here aren't just generic points. They  
**[22:43]** are typed entities like movie, person,  
**[22:46]** genre. And the edges as well aren't just  
**[22:49]** generic connections. They are labeled  
**[22:52]** relationships like you've directed by,  
**[22:54]** you have has Joner, you have has cast,  
**[22:58]** you have acted in, etc.  
**[23:01]** And this is how we also actually think  
**[23:03]** about movies in our head. When someone  
**[23:05]** says Inception, your brain is not  
**[23:08]** pulling a spreadsheet row. Your brain  
**[23:10]** pulls up a web of connections. When I  
**[23:13]** say Inception, your brain thinks of  
**[23:14]** Nolan. Your brain thinks uh DiCaprio  
**[23:18]** starred in Inception. Your brain thinks  
**[23:21]** DiCaprio was also in Catch Me If You  
**[23:23]** Can. And without realizing, you start  
**[23:26]** traversing these notes and  
**[23:27]** relationships.  
**[23:30]** So okay once we have built a knowledge  
**[23:32]** graph with these entities and  
**[23:34]** relationships we now need a mechanism to  
**[23:37]** retrieve the structured data so that we  
**[23:40]** can add it to our context and it can  
**[23:43]** help agents provide better results and  
**[23:47]** this entire process of actually  
**[23:49]** incorporating knowledge graphs is called  
**[23:52]** graph rag.  
**[23:54]** An agentic graph rag is basically an AI  
**[23:57]** framework where you combine the  
**[23:59]** structured reasoning of knowledge graphs  
**[24:02]** with the autonomous goal oriented  
**[24:04]** decision making of LLM based agents.  
**[24:08]** And you might be wondering how we  
**[24:10]** actually query a knowledge graph. So to  
**[24:13]** do that we write a graph query. And  
**[24:15]** since we are using Neo4j as our graph  
**[24:17]** database the query is in cipher. But  
**[24:21]** don't worry uh you don't have to learn  
**[24:23]** to write cipher queries because LLMs are  
**[24:26]** intelligent enough to convert our  
**[24:28]** natural language questions into cipher  
**[24:31]** and the graph will in turn make our LLM  
**[24:34]** generate better results by giving it  
**[24:37]** structured connected verifiable facts  
**[24:40]** instead of fuzzy text matches. So you  
**[24:44]** can actually see how Genai is helping us  
**[24:47]** make graph data accessible which in turn  
**[24:50]** is actually enhancing our GI  
**[24:52]** applications.  
**[24:55]** So now let's go back to our code base.  
**[24:58]** So I'll require some new tools for our  
**[25:00]** AI agent. The first tool is the get  
**[25:03]** graph schema which is going to provide  
**[25:05]** me all the details about the structure  
**[25:08]** of the graph including node types,  
**[25:10]** relationships and their properties.  
**[25:13]** The second tool is the execute cipher  
**[25:16]** tool which is allowing the agent to read  
**[25:19]** uh to run basically all our cipher  
**[25:21]** queries against the neo-4j database and  
**[25:24]** retrieve the results.  
**[25:27]** And the third thing is we are  
**[25:29]** initializing our agent. We are providing  
**[25:31]** it the same LLM back end along with both  
**[25:34]** our new tools and the system prompt. So  
**[25:38]** now let us see how things are happening  
**[25:41]** under the hood. Once the agent gets the  
**[25:43]** query, it immediately goes I need to  
**[25:46]** understand the graph structure first and  
**[25:48]** then generate a cipher query and then  
**[25:51]** execute it. So then it is going ahead  
**[25:55]** calling our first tool call which is the  
**[25:57]** get graph schema and it is uh figuring  
**[26:01]** out how the database looks like once it  
**[26:04]** gets back the full structure.  
**[26:06]** So which will be your nodes, your  
**[26:09]** relationships,  
**[26:10]** everything. The agent now knows exactly  
**[26:13]** what it is working with. It knows what  
**[26:15]** properties it can filter on, what  
**[26:17]** relationships it can traverse and what  
**[26:20]** nodes it can match. It then goes ahead  
**[26:24]** and uh calls our execute cipher. So what  
**[26:27]** it does is it is taking the user's five  
**[26:30]** constraint looking at the schema it just  
**[26:33]** received. The LLM is writing the cipher  
**[26:36]** query so that all of it can be  
**[26:38]** addressed. Um, and it is running the  
**[26:42]** tool.  
**[26:44]** Then our agent is evaluating the result  
**[26:47]** and responding. And if the results come  
**[26:50]** back empty or didn't look look right for  
**[26:53]** some reason, the agent is going to loop  
**[26:55]** back, refine the query, and it is going  
**[26:57]** to try again. And that's our agentic  
**[27:01]** loop. So if you compare this to the rag  
**[27:04]** flow, the rag agent just made one tool  
**[27:06]** call a text search. But this agent is  
**[27:08]** making two tool calls, schema first and  
**[27:12]** then a precise query. It is learning the  
**[27:15]** data structure first before writing the  
**[27:18]** cipher query.  
**[27:20]** So this is how actually our generated  
**[27:23]** cipher looks like. And now let us  
**[27:27]** quickly look at the demo.  
**[27:32]** So you can see here once I enter the  
**[27:34]** prompt behind the scenes the ondevice  
**[27:37]** trans agent is calling the get graph  
**[27:39]** schema tool and once it is receiving the  
**[27:42]** get graph schema response it is taking  
**[27:45]** the user constraints combining with the  
**[27:47]** schema and using our 3.7 set model to  
**[27:51]** generate the cipher query. Then it is  
**[27:54]** sending that cipher square query to the  
**[27:57]** execute cipher tool.  
**[28:00]** And in case say for example the tool  
**[28:02]** fails to obtain a response the agent is  
**[28:05]** regenerating the cipher and calling the  
**[28:08]** execute cipher tool again. And this is  
**[28:10]** exactly the agentic loop that we were  
**[28:13]** discussing about earlier.  
**[28:17]** And after all this has been done after  
**[28:19]** it gets the response you can see the  
**[28:22]** response here is being displayed. So it  
**[28:25]** has given us five movie options which  
**[28:29]** match all of our five criteria.  
**[28:36]** So uh now coming to the key takeaways.  
**[28:39]** So the first thing is that you don't  
**[28:41]** always need a better or a more expensive  
**[28:43]** model. So like you could see in this  
**[28:46]** case we use the same model for all our  
**[28:48]** three attempts and if you have better  
**[28:51]** tools  
**[28:52]** you can get better answers if like we  
**[28:56]** saw in our example. The only thing that  
**[28:58]** we changed all across our three example  
**[29:00]** was the tools array.  
**[29:02]** The second thing is when your data has  
**[29:06]** relationships you can use a graph.  
**[29:09]** Vector search finds things that sounds  
**[29:12]** familiar but knowledge graph can find  
**[29:15]** things that are actually connected. And  
**[29:17]** for our multihop constraint rich  
**[29:19]** queries, this is the difference between  
**[29:22]** guessing and knowing. And not only this,  
**[29:24]** the answer is also auditable. It is also  
**[29:27]** easy to explain as you can trace  
**[29:30]** knowledge graph through notes and edges.  
**[29:33]** And the third is ondevice agents are  
**[29:35]** simpler than you think. you like you saw  
**[29:38]** in our example just a strands SDK with a  
**[29:41]** model two tools and the system prompt is  
**[29:44]** all what it took to build this agentic  
**[29:47]** app. The agent runs completely grind  
**[29:50]** side and it streams directly to the  
**[29:52]** user.  
**[29:54]** And with this we have come to an end for  
**[29:57]** this session. So you can follow me on  
**[29:59]** LinkedIn and my Judithub handle. And if  
**[30:02]** you want to learn more about how you can  
**[30:04]** leverage Neo4j and Amazon Bedrock for an  
**[30:09]** explanable, secure and connected  
**[30:11]** generative AI solution. You can check  
**[30:13]** out this blog.  