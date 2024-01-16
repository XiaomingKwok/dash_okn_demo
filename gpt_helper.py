
node_properties_query = """
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE NOT type = "RELATIONSHIP" AND elementType = "node"
WITH label AS nodeLabels, collect(property) AS properties
RETURN {labels: nodeLabels, properties: properties} AS output

"""

rel_properties_query = """
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE NOT type = "RELATIONSHIP" AND elementType = "relationship"
WITH label AS nodeLabels, collect(property) AS properties
RETURN {type: nodeLabels, properties: properties} AS output
"""

rel_query = """
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE type = "RELATIONSHIP" AND elementType = "node"
RETURN {source: label, relationship: property, target: other} AS output
"""

from neo4j import GraphDatabase
from neo4j.exceptions import CypherSyntaxError
import openai
# from openai import OpenAI
import os

openai_key = ""
# client = OpenAI(api_key=openai_key)


def schema_text(node_props, rel_props, rels):
    return f"""
  This is the schema representation of the Neo4j database.
  Node properties are the following:
  {node_props}
  Relationship properties are the following:
  {rel_props}
  Relationship point from source to target nodes
  {rels}
  Make sure to respect relationship types and directions
  """


class Neo4jGPTQuery:
    def __init__(self, url, user, password, openai_api_key):
        self.driver = GraphDatabase.driver(url, auth=(user, password), database="okn2")
        openai.api_key = openai_api_key
        # construct schema
        self.schema = self.generate_schema()


    def generate_schema(self):
        node_props = self.query_database(node_properties_query)
        rel_props = self.query_database(rel_properties_query)
        rels = self.query_database(rel_query)
        input_schema = schema_text(node_props, rel_props, rels)
        print(input_schema)
        return input_schema

    def refresh_schema(self):
        self.schema = self.generate_schema()

    def get_system_message(self):
        return f"""
        Task: Generate Cypher queries to query a Neo4j graph database based on the provided schema definition.
        Instructions:
        Use only the provided relationship types and properties.
        When dealing with city names, construct the queries to allow for partial or inexact matches. Utilize Cypher's string functions like CONTAINS, STARTS WITH, ENDS WITH, or regular expressions for this purpose.
        Do not use any other relationship types or properties that are not provided.
        If you cannot generate a Cypher statement based on the provided schema, explain the reason to the user.
        Schema:
        {self.schema}

        The Variable nodes represents questions in the survey, and the description holds the content of each question. Each person's response is stored in the 'ANSWERED' relationship. This relationship includes a 'name' property that signifies a 'Yes' or 'No' response.

        Note: Do not include any explanations or apologies in your responses.
        Ensure that the queries are efficient and optimized for performance, particularly when using pattern matching or regular expressions.
        """
    
    def format_neo_results(self, neo_res):
        if not neo_res or not isinstance(neo_res, list):
            return "No results or invalid format."

        # Assuming the first row contains column headers
        headers = neo_res[0]
        formatted_result = "Results:\n"

        # Formatting each row of the result
        for row in neo_res[1:]:  # Skipping header row
            row_str = ', '.join([f"{headers[i]}: {value}" for i, value in enumerate(row)])
            formatted_result += f"- {row_str}\n"

        return formatted_result

    
    # def generate_nl_answer(self, question, neo_res):
    #     formatted_neo_res = self.format_neo_results(neo_res)
    #     return f"""
    #     Convert the results of a Cypher query into a natural language explanation. 

    #     Original question: "{question}"

    #     Neo4j query results:
    #     {formatted_neo_res}

    #     Based on these results, provide a clear and concise summary or explanation in natural language.
    #     """

    def query_database(self, neo4j_query, params={}):
        with self.driver.session() as session:
            result = session.run(neo4j_query, params)
            output = [r.values() for r in result]
            output.insert(0, result.keys())
            return output

    def construct_cypher(self, question, history=None):
        messages = [
            {"role": "system", "content": self.get_system_message()},
            {"role": "user", "content": question},
        ]
        # Used for Cypher healing flows
        if history:
            messages.extend(history)

        completion = openai.chat.completions.create(
            model="gpt-4",
            temperature=0.0,
            max_tokens=1000,
            messages=messages
        )
        return completion.choices[0].message.content
    
    def convert_neo_results_to_nl(self, question, neo_res, history=None):
        # Format the Neo4j results
        formatted_neo_res = self.format_neo_results(neo_res)

        # Construct the prompt for GPT-4
        prompt = f"""
        Convert the results of a Cypher query into a natural language explanation. 

        Original question: "{question}"

        Neo4j query results:
        {formatted_neo_res}

        Based on these results, provide a clear and concise summary or explanation in natural language.
        """

        # Prepare the messages for GPT-4
        messages = [
            {"role": "system", "content": "Your task is to convert the following database query results into a natural language explanation."},
            {"role": "user", "content": prompt},
        ]

        # Include history if available
        if history:
            messages.extend(history)

        # Use GPT-4 to generate the natural language answer
        completion = openai.chat.completions.create(
            model="gpt-4",
            temperature=0.0,
            max_tokens=1000,
            messages=messages
        )

        # Return the natural language answer
        return completion.choices[0].message.content

    def extract_city_data(self, question, answer, history=None):
        # Construct the prompt for GPT-4
        prompt = f"""
        Task: Analyze the provided question and answer to extract city-related data. Then, format the data into a JSON object where the key is the city's CBSA code, and the value is the statistical data related to the city.

        Example JSON format:
        {{
            "12120": 201.3,
            "27530": 270.7,
            "42820": 297.1,
            "11500": 190.5,
            "37120": 133.9,
            "21460": 121.2,
            "22520": 211.8,
            "10760": 66.8
        }}

        Here are some CBSA codes for reference:
        - San Antonio-New Braunfels, TX: 41700
        - Los Angeles-Long Beach-Anaheim, CA: 31080
        - Detroit-Warren-Dearborn, MI: 19820
        - Pittsburgh, PA: 38300
        - Atlanta-Sandy Springs-Roswell, GA: 12060
        - San Francisco-Oakland-Hayward, CA: 41860
        - All other metropolitan areas: 99998
        - Cincinnati, OH-KY-IN: 17140
        - Oklahoma City, OK: 36420
        - San Jose-Sunnyvale-Santa Clara, CA: 41940
        - Houston-The Woodlands-Sugar Land, TX: 26420
        - Richmond, VA: 40060
        - Dallas-Fort Worth-Arlington, TX: 19100
        - Philadelphia-Camden-Wilmington, PA-NJ-DE-MD: 37980
        - Tampa-St. Petersburg-Clearwater, FL: 45300
        - New Orleans-Metairie, LA: 35380
        - Baltimore-Columbia-Towson, MD: 12580
        - Riverside-San Bernardino-Ontario, CA: 40140
        - Rochester, NY: 40380
        - Memphis, TN-MS-AR: 32820
        - Denver-Aurora-Lakewood, CO: 19740
        - Las Vegas-Henderson-Paradise, NV: 29820
        - Portland-Vancouver-Hillsboro, OR-WA: 38900
        - Kansas City, MO-KS: 28140
        - Chicago-Naperville-Elgin, IL-IN-WI: 16980
        - Seattle-Tacoma-Bellevue, WA: 42660
        - Milwaukee-Waukesha-West Allis, WI: 33340
        - Cleveland-Elyria, OH: 17460
        - Minneapolis-St. Paul-Bloomington, MN-WI: 33460
        - Raleigh, NC: 39580
        - Birmingham-Hoover, AL: 13820
        - New York-Newark-Jersey City, NY-NJ-PA: 35620
        - Boston-Cambridge-Newton, MA-NH: 14460
        - Miami-Fort Lauderdale-West Palm Beach, FL: 33100
        - Washington-Arlington-Alexandria, DC-VA-MD-WV: 47900
        - Phoenix-Mesa-Scottsdale, AZ: 38060

        Original question: "{question}"
        Answer: "{answer}"

        Based on the question and answer, extract the relevant city data and construct the JSON object.
        """

        # Prepare the messages for GPT-4
        messages = [
            {"role": "system", "content": "Extract city data from the question and answer and format it into a JSON object."},
            {"role": "user", "content": prompt},
        ]

        # Include history if available
        if history:
            messages.extend(history)

        # Use GPT-4 to generate the response
        completion = openai.chat.completions.create(
            model="gpt-4",
            temperature=0.5,
            max_tokens=150,
            messages=messages
        )

        # Return the formatted response
        return completion.choices[0].message.content


    def run(self, question, history=None, retry=True):
        # Construct Cypher statement
        cypher = self.construct_cypher(question, history)
        print(cypher)
        try:
            neo_res = self.query_database(cypher)
            nl_res = self.convert_neo_results_to_nl(question, neo_res, history)
            city_res = self.extract_city_data(question, nl_res)
            return nl_res, city_res
        # Self-healing flow
        except CypherSyntaxError as e:
            # If out of retries
            if not retry:
              return "Invalid Cypher syntax", ""
        # Self-healing Cypher flow by
        # providing specific error to GPT-4
            print("Retrying")
            return self.run(
                question,
                [
                    {"role": "assistant", "content": cypher},
                    {
                        "role": "user",
                        "content": f"""This query returns an error: {str(e)} 
                        Give me a improved query that works without any explanations or apologies""",
                    },
                ],
                retry=False
            )

if __name__ == "__main__":

    gds_db = Neo4jGPTQuery(
        url="bolt://localhost:7687",
        user="neo4j",
        password="11111111",
        openai_api_key=openai_key,
    )

    res_1 = gds_db.run("""
    Who is the actor who has participated in the most movies?
    """)

    print(res_1)