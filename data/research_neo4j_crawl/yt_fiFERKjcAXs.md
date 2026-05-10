# Transcript: https://www.youtube.com/watch?v=fiFERKjcAXs

**Language:** English (auto-generated) (en) — auto-generated
**Snippets:** 568

---

**[00:08]** Hello everyone. So this session agent  
**[00:13]** rag meets a neo4j multihop reasoning  
**[00:16]** over scientific knowledge graphs by  
**[00:19]** Annabel Banchero and John Leel Long.  
**[00:23]** Over to you guys.  
**[00:25]** >> Thank you very much. Um we're very happy  
**[00:28]** to be here today. um to talk about this  
**[00:31]** uh very interesting project and how we  
**[00:33]** combined  
**[00:35]** multi to multi-tool  
**[00:38]** agent and uh and graph knowledge based  
**[00:41]** uh information. Um just one word about  
**[00:45]** uh the company we work with it's  
**[00:47]** echometrics. Uh we build solutions for  
**[00:51]** different type of clients. Uh we have  
**[00:53]** different offices around the world. Um  
**[00:55]** and uh yeah we we quite tech agnostic um  
**[00:59]** and we we do custom based um um  
**[01:04]** solutions  
**[01:06]** and we did this project with INRA which  
**[01:09]** is a French national institute um on  
**[01:13]** agriculture and the environment and we  
**[01:15]** especially did that project. No no can  
**[01:17]** you go back?  
**[01:18]** >> Yeah. Sorry, I will have to  
**[01:24]** >> we did this project with the open  
**[01:25]** science  
**[01:26]** >> because otherwise it will change. Sorry.  
**[01:29]** >> Yeah. And the open science department is  
**[01:33]** how to um um talk about the science that  
**[01:37]** is being done at INRAY.  
**[01:40]** Uh ENRAY has more than 200 2,100  
**[01:44]** researchers, lots of engineers and  
**[01:45]** technicians as well. and they publish  
**[01:48]** more than 5,000 publication per year um  
**[01:52]** with different uh other uh institutions  
**[01:56]** and uh they have uh project that are  
**[01:59]** financed by different uh financial  
**[02:02]** institutions and they usually need to um  
**[02:06]** find information within that huge  
**[02:08]** database  
**[02:10]** and it's usually not just an answer to  
**[02:12]** scientific questions but it's more like  
**[02:15]** uh what is the most known researcher in  
**[02:18]** that topic or um what is what project  
**[02:21]** have been funded by this fund or um how  
**[02:26]** many publications did in produced on  
**[02:28]** that topic. So it's it's a bit more  
**[02:30]** complex information and they came to us  
**[02:33]** asking could we leverage new knowledge  
**[02:36]** management technologies to improve the  
**[02:39]** retrieval of these science related  
**[02:41]** questions but not completely not purely  
**[02:43]** scientific  
**[02:45]** and um to do so we started by uh  
**[02:49]** implementing uh knowledge based um um  
**[02:53]** system and we went for um yeah you can  
**[02:58]** you  
**[02:59]** move to the next one. We moved to um a  
**[03:02]** graph knowledge based. Uh we used that  
**[03:05]** to unify three different data format. We  
**[03:08]** had a lot of table of data about the  
**[03:10]** publications. Um we had who published  
**[03:14]** it, when in what journal  
**[03:17]** um and all the information around the  
**[03:20]** publications. We also had information  
**[03:22]** about the funding, the projects, uh the  
**[03:25]** institutions, lots of different tables  
**[03:27]** around uh around all this. We also had  
**[03:30]** unstructured text, the publications  
**[03:32]** themselves. And we had a lexical tree of  
**[03:36]** all the concept and subcon  
**[03:39]** concepts um that was all well organized  
**[03:42]** into this this lexical tree and we  
**[03:45]** combined all of those into one unified  
**[03:49]** knowledge graph. Here a really important  
**[03:52]** point was that um for tabular data it  
**[03:56]** was really easy for us to find exactly  
**[03:59]** the right combinations of relationships  
**[04:03]** between entities. Usually it's uh one of  
**[04:06]** the most complicated step of make using  
**[04:09]** a knowledge graph in an AI application  
**[04:12]** is making the knowledge graph itself.  
**[04:14]** Here it was really fit for this use case  
**[04:19]** and for the unstructured text um same as  
**[04:24]** we used um scientific papers it was very  
**[04:28]** structured informations with like  
**[04:30]** keywords usually at the same place and  
**[04:35]** authors at the same place and so on. So  
**[04:38]** it was really easy to navigate. And then  
**[04:41]** for the leical tree um it was to make a  
**[04:45]** link between their uh way of interacting  
**[04:49]** with the data and uh our uh knowledge  
**[04:53]** graph that we made from that data to use  
**[04:56]** the same words and the same definitions  
**[04:58]** that these very specific and technical  
**[05:02]** people use.  
**[05:07]** So here um this is the knowledge graph  
**[05:10]** we made  
**[05:13]** um with uh about uh 10 different uh  
**[05:18]** types of nodes uh centers centered  
**[05:22]** around the publication node um with  
**[05:26]** about 400,000 nodes in total and a  
**[05:30]** little bit more than 1 million edges. um  
**[05:34]** we centered everything around  
**[05:36]** publications to reflect the way we  
**[05:38]** extracted the data from the different  
**[05:40]** papers and also because it made sense um  
**[05:44]** in this particular use case. So lots of  
**[05:48]** different authors. Um and uh just to  
**[05:52]** explain a little  
**[05:54]** little bit more a few different nodes,  
**[05:58]** keywords where the keyword um um  
**[06:03]** declarated by the authors when  
**[06:06]** publishing their work. Uh so it's  
**[06:09]** written by them. Um and the concept and  
**[06:15]** domain that you can  
**[06:17]** can see here in purple and green are  
**[06:19]** from the the tree that they had. We took  
**[06:24]** every um node of their tree that had the  
**[06:29]** different uh subdomains um after it and  
**[06:35]** called it a domain. And then we took all  
**[06:37]** the leaves of these uh treel like  
**[06:40]** structures with the definitions and call  
**[06:43]** them concepts.  
**[06:45]** Um the other ones are pretty  
**[06:48]** self-explanatory. Software is the  
**[06:50]** software used in the scientific  
**[06:52]** publications. Data set are the different  
**[06:54]** data used in the scientific publication.  
**[06:58]** Yeah.  
**[07:00]** Then this is um an example uh an extract  
**[07:05]** of the graph um that we constructed  
**[07:13]** um with with a publication in the  
**[07:18]** journal. It was  
**[07:20]** the  
**[07:37]** Uh this graph um  
**[07:41]** we made the NLM agents with access to  
**[07:45]** several tools.  
**[07:48]** sorry, several tools um with a knowledge  
**[07:52]** graph tool to interact directly with the  
**[07:54]** knowledge graph but also uh two other  
**[07:56]** tools and I will detail each one of them  
**[07:59]** next um to uh find uh entry point into  
**[08:04]** the graph and then a fourth one um more  
**[08:07]** complex uh that we outcoded with uh some  
**[08:10]** rules to identify experts uh in the  
**[08:14]** graph. That was one of the big uh use  
**[08:17]** cases that they gave us was to be able  
**[08:20]** to identify expertise uh in different  
**[08:23]** topics among all of their researchers,  
**[08:26]** all of their university.  
**[08:30]** So for the first um tool  
**[08:34]** um it was just a  
**[08:39]** cipher query tool.  
**[08:42]** So  
**[08:46]** we allowed the model to write directly  
**[08:50]** on the graph of course. So here is one  
**[08:52]** example pretty complex to really show  
**[08:55]** how good um LLM can be with  
**[09:00]** writing knowledge graphs. Here for this  
**[09:03]** particular example, we used a recent  
**[09:06]** open AAI model, but we we coded the  
**[09:09]** entire application with open source or  
**[09:14]** open weight  
**[09:16]** models. So it could also work with the  
**[09:19]** last deepseek model or any agent capable  
**[09:23]** model.  
**[09:26]** So yeah, pretty straightforward. And  
**[09:28]** then um we we were looking for ways to  
**[09:35]** um give ideas to the model uh to find  
**[09:40]** better entry points into the graph um  
**[09:42]** based on the words and the semantic  
**[09:45]** inside of uh the chunk we used to  
**[09:48]** represent each publication which was um  
**[09:52]** title, abstract, introduction and  
**[09:54]** conclusion that we extracted from the  
**[09:57]** all of the publication. we scrapped from  
**[09:59]** the internet.  
**[10:02]** Um and then we used uh an hybrid search  
**[10:06]** pipeline uh that you can see here with  
**[10:10]** um the query. Then we represent the  
**[10:13]** query with two different vector. one uh  
**[10:16]** semantic vector. So classic embedding uh  
**[10:19]** by a BM coder to represent really the  
**[10:23]** meaning behind the the different words  
**[10:25]** of the query and then um in parallel we  
**[10:29]** create a sparse uh vector to represent  
**[10:33]** uh which word are or are not uh  
**[10:37]** contained in the query. So uh to uh be  
**[10:41]** able to tell uh if specific words are in  
**[10:46]** common between the query and the  
**[10:48]** different documents. Those are very  
**[10:51]** complimentary because the first one is  
**[10:53]** able to really um have a feeling for the  
**[10:56]** the meaning behind the different words  
**[10:58]** and synonyms and the negations and so  
**[11:02]** on. And the the second one is very  
**[11:04]** important in this context because lots  
**[11:06]** of words don't mean anything for beoder.  
**[11:11]** For example, um names uh or very  
**[11:15]** technical um uh vocabulary are not  
**[11:20]** present in the the training data of the  
**[11:24]** bianer. So it's really important to have  
**[11:26]** both. Um and then we used a a step of  
**[11:30]** reanking to um merge efficiently those  
**[11:35]** two and have really the most relevant  
**[11:37]** publication. So this is another tool uh  
**[11:42]** the LLM agent have access to to find an  
**[11:46]** entry point and usually to use the ID  
**[11:52]** it  
**[11:54]** um at the end of this line to write  
**[11:56]** cipher code and um on the same ID. Uh  
**[12:01]** this is another tool um written with  
**[12:05]** Neo4j  
**[12:06]** uh to uh find um different concept and  
**[12:12]** keywords. Um so concept are the  
**[12:14]** vocabulary they usually use and keywords  
**[12:17]** are the declared the keyword  
**[12:21]** by each authors of their publications.  
**[12:25]** And so uh this allow the model to find  
**[12:29]** the same here entry point into the graph  
**[12:33]** to uh really have a a topic entry that  
**[12:37]** will lead to several publications. So  
**[12:40]** for example climate change or things  
**[12:42]** like that for the keywords um we  
**[12:45]** understand directly how it works. And  
**[12:48]** for the concept, one thing uh maybe I  
**[12:50]** was not clear about is we uh detected if  
**[12:55]** the concept appeared in the chunks that  
**[12:59]** we selected from the documents. So  
**[13:01]** again, title, abstract, introduction,  
**[13:04]** conclusion. Um, and if so, we created uh  
**[13:10]** the the link  
**[13:14]** uh the the edge, sorry. uh between uh  
**[13:17]** the concept and the publication,  
**[13:21]** the LLM agent has access to uh which is  
**[13:26]** a more complex, more hardcoded based on  
**[13:30]** rules we decided on with them um to  
**[13:36]** identify experts in their field. So it  
**[13:40]** calls uh several times each of the other  
**[13:43]** tools um in  
**[13:47]** in code in hardcoded program uh and then  
**[13:51]** give a consolidated score of uh the  
**[13:55]** expertise of each researcher on a given  
**[13:59]** uh topic.  
**[14:04]** So here we will show you a few examples  
**[14:07]** to really uh ponder how good uh this  
**[14:12]** approach is compared to classical  
**[14:18]** retro generation.  
**[14:20]** >> Thank you very much.  
**[14:21]** >> And then we will show you a few concrete  
**[14:24]** example of demon.  
**[14:27]** >> Yeah, we sometimes we're losing you. Um  
**[14:31]** um so yes. So measuring performance of  
**[14:34]** these kinds of uh of systems are pretty  
**[14:38]** tricky uh because they don't do things  
**[14:40]** the same way and they don't uh  
**[14:42]** necessarily have the same um the same  
**[14:45]** results. So we tried to give you some  
**[14:49]** qualitative examples of the way uh a  
**[14:52]** classic rag would respondse to some  
**[14:54]** questions um an agentic rag and our  
**[14:58]** agentic knowledge based um graph  
**[15:00]** knowledgebased rag. Let's uh take one uh  
**[15:05]** example for example this question which  
**[15:08]** research units publish the most on  
**[15:10]** climate change and which authors  
**[15:12]** contribute most of these paper. So here  
**[15:15]** we have two different questions within  
**[15:17]** one. Uh so it's a multihop and  
**[15:20]** definitely the classic rag is just not  
**[15:22]** able to answer the question at all. Uh  
**[15:24]** the classic rag would be just based on  
**[15:26]** the publications themselves. Um and his  
**[15:30]** reply its reply is to just ask for more  
**[15:33]** information um to the user. The aentigra  
**[15:38]** manages to extract a bit more context  
**[15:40]** but also admits that it completely lacks  
**[15:43]** uh information to answer the questions.  
**[15:48]** What our uh system does is that it would  
**[15:51]** first extract the keywords and the  
**[15:53]** concepts that are related to climate  
**[15:55]** change. From these keywords and concept  
**[15:57]** concept it would extract the  
**[15:59]** publications that are related to these  
**[16:01]** and then we'll research the research  
**[16:04]** units and authors that are affiliated to  
**[16:06]** these publications and then it would  
**[16:08]** rank all of these research units and  
**[16:11]** authors by the number of publications.  
**[16:13]** So it's able to do this multi up uh  
**[16:15]** looking for um information within the  
**[16:18]** graph knowledge base through through  
**[16:20]** these different entry points and uh it's  
**[16:23]** able to answer this this complex  
**[16:24]** question. If we take another  
**[16:27]** >> just  
**[16:28]** to be extra clear with the different  
**[16:31]** definitions in our experimentation for  
**[16:34]** classic rag we used an outcoded pipeline  
**[16:37]** that will just do one retrieval call  
**[16:40]** based on the user query and that's it  
**[16:42]** with the top 10 let's say we use top 15  
**[16:46]** um extract from the the text of the  
**[16:49]** knowledge base. Then for agentic rag,  
**[16:52]** it's the same, but it's just the LLM  
**[16:54]** that has access to the retrieval tool.  
**[16:57]** And then for agentic kgbased rag, it's  
**[17:00]** what I what I explained just before.  
**[17:07]** So if we take another example, um what  
**[17:10]** is the oldest publication available in  
**[17:12]** your database? Um here we just compare  
**[17:15]** the agent rag and and our solution. um  
**[17:18]** the response that the agent rag will  
**[17:20]** give is basically I can't pinpoint a  
**[17:23]** single oldest record. Uh it doesn't have  
**[17:25]** that meta data information that would  
**[17:28]** allow it to uh to pinpoint that  
**[17:31]** information. Whereas our solution is  
**[17:34]** giving the answer that is uh uh legume  
**[17:38]** nautles uh on published on the 1 of  
**[17:41]** January 2029 uh 2019  
**[17:44]** uh because it is using the research  
**[17:47]** graph um and is able to then rank  
**[17:50]** publications by date and then give the  
**[17:52]** oldest u publication that he has in this  
**[17:55]** database.  
**[17:57]** So this question even if it's not a  
**[17:59]** multihop and it's quite it's more simple  
**[18:02]** than the previous example uh an agent  
**[18:04]** agentic rag is still not able to to to  
**[18:07]** provide a correct answer on this. We  
**[18:10]** have another example to give you  
**[18:14]** uh is your current knowledge base how  
**[18:16]** many articles were published in 2022.  
**[18:19]** Same idea I think we can we can go a bit  
**[18:23]** faster on this one.  
**[18:26]** Uh another question, another question  
**[18:28]** would be that is a bit more complex. Um  
**[18:31]** who are the researchers in common  
**[18:32]** between the two research units Paris and  
**[18:36]** the L2A?  
**[18:39]** Uh here the identic did not even  
**[18:42]** understand what the L2A was and asked  
**[18:45]** for uh more information from the user.  
**[18:48]** And here hybrid search is definitely not  
**[18:50]** appropriate to to to answer these kind  
**[18:53]** of questions. Our solution does give  
**[18:56]** sorry just yeah gives the proper answer  
**[18:59]** with the two um two researchers that are  
**[19:02]** in common between the two research  
**[19:04]** units. It is able to do multiple queries  
**[19:07]** to gather the information and then to  
**[19:09]** compare uh that information and um I  
**[19:12]** think we can see more details in the  
**[19:14]** next uh question bit how it works.  
**[19:17]** Another complex question  
**[19:20]** um where we have uh what researchers  
**[19:23]** published at least four papers in 2020  
**[19:26]** but had zero publications in 2021 and  
**[19:28]** then asked to rank them by number of  
**[19:31]** publications in 2020.  
**[19:33]** Again the aentic quag is absolutely not  
**[19:36]** able to answer this question. It  
**[19:38]** completely in addition completely uh  
**[19:40]** struggles with negative queries.  
**[19:43]** um finding what is not there is  
**[19:45]** extremely difficult for the agent rag  
**[19:48]** where whereas our our solution um does  
**[19:51]** that very well. Uh it is able using this  
**[19:55]** multihop and using the knowledge graph  
**[19:57]** to extract all the information and then  
**[19:59]** to rank this um this information into  
**[20:02]** the the table that you can see here on  
**[20:04]** the right.  
**[20:09]** Um  
**[20:10]** >> before show showing you  
**[20:13]** >> we have we have questions I think it is  
**[20:15]** interesting to leave some some time for  
**[20:18]** the questions in the end.  
**[20:19]** >> Yeah. Okay.  
**[20:20]** >> Yeah.  
**[20:22]** >> Just so one thing before going to the  
**[20:24]** demonstrations. It's really important  
**[20:27]** for us those few things because for  
**[20:32]** clients that we do rag for um they don't  
**[20:36]** understand exactly how rag rich  
**[20:39]** generation works. So it's um often  
**[20:43]** counterintuitive to try to explain to  
**[20:46]** them it cannot know what it doesn't know  
**[20:50]** and to to explain that we cannot have  
**[20:53]** exhaustivity. we cannot count things in  
**[20:56]** the knowledge base and so on. So it's  
**[20:58]** really easier to use these types of um  
**[21:02]** agentic knowledge graph based rag uh  
**[21:06]** because uh it's much more um uh  
**[21:11]** intuitive to understand the limits of  
**[21:14]** the agency.  
**[21:16]** >> Absolutely. And we are we are  
**[21:18]** >> so a few examples maybe you can show  
**[21:22]** >> John Can you hear me? Yeah. One second.  
**[21:24]** Um we are still working on on  
**[21:26]** formalizing a very good um um  
**[21:31]** performance measurement framework uh for  
**[21:34]** this that we could quantify a bit  
**[21:36]** better. Uh all of this we have different  
**[21:38]** dimension as as explained the uh  
**[21:42]** exhaustivity for example and and and all  
**[21:44]** of that. If you have any suggestions  
**[21:46]** we'll be we'll be happy to to look into  
**[21:48]** what you could suggest.  
**[21:52]** uh demonstration now. Thank you.  
**[22:06]** Did we use?  
**[22:15]** Yes. And uh here for examp  
**[22:35]** I I think you're back. Yeah. Maybe start  
**[22:37]** again the demonstration.  
**[22:39]** >> Okay. Wow. There is a a delay then. Um  
**[22:45]** I'm really sorry.  
**[22:50]** Okay. So this is a demonstration. I  
**[22:53]** don't know if you heard what I  
**[22:54]** explained. So I will do it again. It  
**[22:56]** will query iteratively and investigate  
**[22:59]** uh to find the different hopes necessary  
**[23:01]** to um go to the final uh answer uh and  
**[23:05]** to gather informations uh on the the  
**[23:09]** topic. And then it will explain  
**[23:11]** everything it found uh in a clear uh way  
**[23:16]** for the user.  
**[23:25]** Maybe we have time for one other video  
**[23:28]** before going to the questions.  
**[23:30]** >> Yeah. Yes. Because we we we still can't  
**[23:33]** completely hear hear you. Um,  
**[23:36]** so yeah, let let's give that give  
**[23:39]** another example. I think it's a good  
**[23:40]** idea.  
**[23:42]** >> Do do you want to do the voice over? I'm  
**[23:45]** sorry if  
**[23:47]** >> you can't hear me.  
**[23:48]** >> Yeah. So um this is also to show you the  
**[23:51]** type of interface that we've developed  
**[23:53]** alongside the solution. Uh on the left  
**[23:56]** you have um the the interaction uh  
**[24:01]** interface user where you have the system  
**[24:04]** giving its port and explaining each step  
**[24:06]** what it's doing and on the right you  
**[24:08]** have the details of different uh uh  
**[24:12]** queries and uh so you have tables you  
**[24:15]** have graph you have the extract of every  
**[24:17]** single steps so you can check uh the  
**[24:20]** information that is giving so here we  
**[24:23]** asking the top five expert on climate  
**[24:25]** change and you can see on the left that  
**[24:28]** it's thinking about it first of all then  
**[24:30]** it's doing a search expert so using the  
**[24:33]** expert tool uh that the the system has  
**[24:37]** access to um and uh I can't see your  
**[24:41]** screen anymore  
**[24:44]** um but I think it's okay um let's try to  
**[24:48]** let's try to answer some of the the  
**[24:50]** questions from um oh it's  
**[24:56]** Um, okay. So, um, yes. So, you have you  
**[25:01]** have the the final answer on the left,  
**[25:04]** but you can see all of the different um  
**[25:06]** um  
**[25:09]** mid answer on the right. Um, Jean, can  
**[25:12]** do you have a a place where you can show  
**[25:14]** that we can  
**[25:16]** show the graph uh extract as well?  
**[25:24]** Yes. So here is the part of the graph  
**[25:27]** that has been extracted in one of the  
**[25:29]** queries. Uh and we can show this um in  
**[25:33]** the interface as well.  
**[25:37]** Okay. Thank you very much John. We have  
**[25:39]** four minutes. We have a few questions.  
**[25:41]** Um if I go back  
**[25:46]** uh to the beginning um what what  
**[25:50]** actually hear you most of the time. I'm  
**[25:52]** really sorry about  
**[25:55]** >> um so what was there a direct link  
**[25:58]** between papers um tabular data and the  
**[26:00]** tree of concept or did you have to make  
**[26:02]** the mapping yourself? Uh we did the  
**[26:05]** mapping ourselves between the tree of  
**[26:07]** concept and the keywords  
**[26:10]** that were um in the papers. So that has  
**[26:14]** to be a little a little matching there.  
**[26:17]** Um  
**[26:19]** yeah  
**[26:22]** another questions  
**[26:25]** um there's a lot about um  
**[26:30]** about hearing problems another question  
**[26:33]** how did you build the text to cipher  
**[26:35]** model uh you give context from the  
**[26:38]** knowledge graph to the LLM so the text  
**[26:41]** to cipher uh  
**[26:45]** so it's mostly from the the LLM that  
**[26:48]** that does the cipher query.  
**[26:51]** >> Yes. So  
**[26:54]** >> go ahead.  
**[26:57]** >> Yeah. No, sorry. There is a big delay. I  
**[26:59]** think um that we we wrote the schema of  
**[27:03]** the um of the knowledge graph in the  
**[27:06]** system prompt of the LLM agent and then  
**[27:09]** we gave a few short examples uh of  
**[27:14]** different queries and how we were  
**[27:16]** expecting the model to react and this  
**[27:19]** was it and uh it worked uh like a charm.  
**[27:23]** Another  
**[27:25]** question. Any idea of time performances  
**[27:28]** for this model?  
**[27:33]** >> I'm not sure I understand. But if if the  
**[27:35]** question is  
**[27:37]** >> yeah the time it takes  
**[27:38]** >> the time it may it takes to answer a  
**[27:40]** question it's uh the tool calls are um  
**[27:44]** instantaneous. So it just depends on the  
**[27:48]** the speed of the LLM itself. Um, it's  
**[27:53]** really quick.  
**[27:55]** >> It takes a It takes a couple of seconds,  
**[27:57]** but No,  
**[27:58]** >> it's not instantane.  
**[28:00]** >> Yeah,  
**[28:01]** >> it does. It does. I mean, the the tool  
**[28:03]** call themselves are not what is um  
**[28:06]** driving the performance. It's really the  
**[28:09]** the speed of the LLM and the uh Yeah.  
**[28:12]** So, it depends on the API you're using  
**[28:15]** or the the framework, I guess, if it's  
**[28:18]** local.  
**[28:19]** Is there a way to access the slides deck  
**[28:22]** uh later? I think we have no problem  
**[28:24]** sharing it. Uh Jean is is projecting  
**[28:27]** here the QR code for the uh archive um  
**[28:31]** paper and this was presented at um ECAI  
**[28:37]** uh last week couple 10 days ago in  
**[28:41]** Bolognia um as a demo track but we we  
**[28:45]** have no problem sharing the the slides  
**[28:47]** as well. Can you explain in more details  
**[28:50]** how you made the semantic search agent  
**[28:53]** based?  
**[28:55]** >> So I think you you are talking about the  
**[28:58]** uh hybrid search. So um it was  
**[29:04]** to go back on the slide. Yeah it was  
**[29:06]** just uh oh no you you mean search just  
**[29:12]** this part of the pipeline. It's a B  
**[29:15]** encoder. So we we created the different  
**[29:17]** chunks for all the publication then  
**[29:19]** created embeddings for each one of them.  
**[29:22]** Uh and then we used cute rent uh to to  
**[29:25]** query easily with cousin similarity of  
**[29:29]** the vector we created based on the query  
**[29:33]** the LLM wanted to search. Um and then we  
**[29:36]** just compare all of the vectors to find  
**[29:39]** the top k vectors that are the closest  
**[29:42]** to the query.  
**[29:45]** I can see that we have 17.  
**[29:47]** >> This node just this node is really  
**[29:49]** >> Yeah. Sorry.  
**[29:50]** >> No, go ahead. Go ahead. No, go ahead.  
**[29:52]** It's better that you finish the the  
**[29:53]** answer.  
**[29:54]** >> No, no, no. But I there is too much  
**[29:56]** delay.  
**[29:58]** >> Um we will try to answer those questions  
**[30:01]** the the additional questions uh online.  
**[30:05]** Thank you very much for your attention.  
**[30:08]** >> Thank you.  