import json
import os
import argparse
from mcp.server.fastmcp import FastMCP
from serpapi import GoogleSearch


def _get_api_key():
    api_key = os.environ.get("SERPAPI_API_KEY", None)
    if api_key is None:
        raise ValueError("Error! API Key should be provided!")
    else:
        return api_key


SERPAPI_API_KEY = _get_api_key()
mcp = FastMCP("google-maps")


# --- several utilities functions ---
def _make_api_request(params: dict) -> dict:
    """
    Sends a request to SerpApi and returns the JSON response.

    Args:
        params (dict): The parameters for the GoogleSearch API request.

    Returns:
        dict: The raw JSON response data from SerpApi or an error dictionary.
    """
    params["api_key"] = SERPAPI_API_KEY
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        if "error" in results:
            return {"error": results["error"]}
        return results
    except Exception as e:
        return {"error": f"An unexpected error occurred during API request: {e}"}


def _summarize_busyness(data):
    """
    Generates a human-readable summary of busyness for each day of the week.

    Args:
        data (dict): A dictionary containing a "graph_results" key, which holds
                     busyness data for each day of the week.

    Returns:
        str: A formatted string summarizing the busiest and least busy times.
    """
    if not isinstance(data, dict) or "graph_results" not in data:
        return "Error: 'graph_results' key not found or data is invalid."

    graph_results = data.get("graph_results", {})
    summary = "Weekly Busyness Summary:\n\n"

    # Define the order of the days
    days_of_week = [
        "sunday",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
    ]

    # Map for display names
    day_display_names = {
        "sunday": "Sunday",
        "monday": "Monday",
        "tuesday": "Tuesday",
        "wednesday": "Wednesday",
        "thursday": "Thursday",
        "friday": "Friday",
        "saturday": "Saturday",
    }

    for day in days_of_week:
        if day in graph_results:
            daily_data = graph_results[day]

            if not daily_data:
                continue

            max_score = -1
            min_score = float("inf")
            busiest_times = []
            least_busy_times = []

            for item in daily_data:
                score = item.get("busyness_score", 0)

                # Find the busiest times
                if score > max_score:
                    max_score = score
                    busiest_times = [item.get("time", "N/A")]
                elif score == max_score:
                    busiest_times.append(item.get("time", "N/A"))

                # Find the least busy times
                if score < min_score:
                    min_score = score
                    least_busy_times = [item.get("time", "N/A")]
                elif score == min_score:
                    least_busy_times.append(item.get("time", "N/A"))

            # Add summary for the day
            summary += f"--- {day_display_names.get(day, day.capitalize())} ---\n"
            summary += f"**Busiest Time(s)** (Score: {max_score}): {', '.join(busiest_times)}\n"
            summary += f"**Least Busy Time(s)** (Score: {min_score}): {', '.join(least_busy_times)}\n\n"

    return summary.strip()


def _summarize_extensions(data: list):
    """
    Formats a list of extension dictionaries into a human-readable string.

    Args:
        data (list): A list of dictionaries, where each dictionary represents an extension.

    Returns:
        str: A formatted string listing the extensions.
    """
    if not isinstance(data, list):
        return "Error: Extensions data is not a list."

    formatted_strings = "The extension is: \n"
    for extension in data:
        if isinstance(extension, dict) and extension:
            key, value = list(extension.items())[0]
            formatted_strings += f"\t{key}: {value}\n"
    return formatted_strings


def _simple_search(query: str, max_results: int = 10):
    """
    Performs a general Google Maps search and extracts basic information.

    Args:
        query (str): The search query (e.g., "pizza restaurant in London").
        max_results (int, optional): The maximum number of results to return. Defaults to 10.

    Returns:
        list[dict] | dict: A list of dictionaries containing summarized place information,
                           or an error dictionary.
    """
    params = {
        "engine": "google_maps",
        "q": query,
    }

    data = _make_api_request(params)
    if "error" in data:
        return {"error": data["error"]}

    results = []
    if "local_results" in data:
        for item in data["local_results"][:max_results]:
            # Define the keys you're interested in
            keys_to_extract = [
                "title",
                "place_id",
                "address",
                "rating",
                "gps_coordinates",
                "reviews",
                "price",
                "types",
                "open_state",
                "hours",
                "operating_hours",
                "phone",
                "website",
                "extensions",
                "service_options",
                "order_online",
                "user_review",
            ]

            # Use a dictionary comprehension to build place_info
            place_info = {
                key: item.get(key)
                for key in keys_to_extract
                if item.get(key) not in [None, ""]
            }

            results.append(place_info)

    return results


def _google_map_get_place_details(place_id: str) -> dict:
    """
    Fetches detailed information for a single place using its place_id,
    and formats several complex fields like popular times and ratings.

    Args:
        place_id (str): The unique ID of the place to retrieve details for.

    Returns:
        dict: A dictionary containing the detailed and processed place information,
              or an error dictionary.
    """
    if not place_id:
        return {"error": "Invalid place_id provided."}

    params = {
        "engine": "google_maps",
        "place_id": place_id,
    }

    data = _make_api_request(params)
    if "error" in data:
        return data

    place_results = data.get("place_results", {})
    if not place_results:
        return {"error": "No place results found for this place_id."}

    # process rating stars
    rating_summarys = place_results.get("rating_summary")
    if rating_summarys:
        final_string = (
            f"The rating summary for {place_results.get('title', 'this place')}"
        )
        sum_stars = sum(summary.get("amount", 0) for summary in rating_summarys)
        if sum_stars > 0:
            for summary in rating_summarys:
                amount = summary.get("amount", 0)
                stars = summary.get("stars", "N/A")
                rate = (amount * 100 / sum_stars) if sum_stars else 0
                final_string += (
                    f"\n The star {stars} has {amount}, with a rate of {rate:.2f} %"
                )
            place_results["rating_summary"] = final_string

    if "user_review" in place_results:
        place_results["user_reviews"] = place_results["user_reviews"].get(
            "most_relevant", []
        )

    if "pepole_also_search_for" in place_results:
        search_list = place_results.get("pepole_also_search_for", [])
        if search_list and len(search_list) > 0:
            place_results["people_also_search_for"] = search_list[0].get(
                "local_results", []
            )
        else:
            place_results.pop("pepole_also_search_for", None)

    popular_times = place_results.get("popular_times")
    if popular_times:
        place_results["popular_times_summary"] = _summarize_busyness(popular_times)
        del place_results["popular_times"]

    extensions = place_results.get("extensions")
    if extensions:
        place_results["summarize_extensions"] = _summarize_extensions(extensions)
        del place_results["extensions"]

    return place_results


def parse_directions(data):
    """
    Parses a Google Maps directions JSON object into a human-readable string.

    Args:
        data (dict): The dictionary containing directions data.

    Returns:
        str: A formatted string of the directions.
    """
    if "error" in data:
        return f"Error getting directions: {data['error']}"

    output = []

    # Mapping for travel modes
    travel_modes = {
        "6": "Best (Default)",
        "0": "Driving",
        "9": "Two-wheeler",
        "3": "Transit",
        "2": "Walking",
        "1": "Cycling",
        "4": "Flight",
    }

    search_params = data.get("search_parameters", {})
    start_addr = search_params.get("start_addr", "N/A")
    end_addr = search_params.get("end_addr", "N/A")
    travel_mode_code = search_params.get("travel_mode", "6")
    travel_mode_name = travel_modes.get(travel_mode_code, "Unknown Mode")

    output.append(
        f"Here are the travel directions for your journey from {start_addr} to {end_addr} by {travel_mode_name}."
    )
    output.append("---")

    # Check if 'directions' key exists and is not empty
    directions = data.get("directions")
    if not directions:
        return "\n".join(output) + "No detailed directions found."

    for i, route in enumerate(directions):
        route_number = i + 1
        output.append(f"## Route {route_number}:")

        # Add general route info
        formatted_duration = route.get("formatted_duration", "N/A")
        formatted_distance = route.get("formatted_distance", "N/A")
        output.append(f"**Duration:** {formatted_duration}")
        output.append(f"**Distance:** {formatted_distance}")

        # Add route details like 'Fastest route' or 'This route has tolls.'
        extensions = route.get("extensions", [])
        if extensions:
            output.append(f"*(Notes: {', '.join(extensions)})*")

        # Add the 'via' information if available
        via = route.get("via")
        if via:
            output.append(f"**Via:** {via}")

        output.append("\n**Detailed Steps:**")

        # Go through each trip in the route
        trips = route.get("trips", [])
        for trip in trips:
            output.append(
                f"- **{trip.get('title', 'N/A')}** ({trip.get('formatted_duration', 'N/A')}, {trip.get('formatted_distance', 'N/A')})"
            )

            # Add detailed steps for each trip
            details = trip.get("details", [])
            for detail in details:
                output.append(
                    f"  - {detail.get('title', 'N/A')} ({detail.get('formatted_distance', 'N/A')})"
                )
        output.append("---")

    return "\n".join(output)


# --- mcp tools ---
# mcp tools for searching
@mcp.tool()
def googlemap_search_places(
    query: str, max_results: int = 10, structured=False
) -> list[dict] | str:
    """
    Performs a general, fuzzy search for places on Google Maps and returns basic place information.

    Args:
        query (str): The search query, supporting fuzzy searches (e.g., "pizza restaurant in London" or "High School in Nanjing").
        max_results (int, optional): The maximum number of search results to retrieve. Defaults to 10.
        structured (bool, optional): If True, returns the results as a list of dictionaries (List[Dict]).
                                     If False, returns a human-readable formatted string. Defaults to False.

    Returns:
        list[dict] | str: A list of basic place information dictionaries (if structured=True)
                          or a string containing a summary of the results.
    """
    try:
        if not query:
            return "Error: Query cannot be empty."

        # get search results
        results = _simple_search(query=query, max_results=max_results)
        if "error" in results:
            return results["error"]

        final_return_string = (
            f"The Basic information for the query: {query} with {len(results)} results"
        )
        # write into json strings
        for index, result in enumerate(results):
            final_return_string += f"\n\n========================= SEARCH RESULT {index+1} ========================="
            final_return_string += f"\n{json.dumps(result,indent=2,ensure_ascii=False)}"
    except Exception as e:
        return {"error": f"Request failed: {e}"}
    if structured:
        return results
    else:
        # for user cases
        return final_return_string


@mcp.tool()
def google_map_get_place_details(query: str, is_accurate_id=False) -> str:
    """
    Retrieves detailed information for a specific place. It can use either a fuzzy search query
    (to get the details of the top result) or a direct place_id.

    Args:
        query (str): The fuzzy search query (e.g., "Eiffel Tower") OR the exact place_id.
        is_accurate_id (bool, optional): If True, treats the query as a precise place_id.
                                         If False (default), performs a search and uses the
                                         place_id of the top result. Defaults to False.

    Returns:
        str: A JSON formatted string containing the comprehensive details of the place,
             including popular times, rating summaries, and extensions.
    """
    try:
        if not query:
            return "Error: Query cannot be empty."

        if is_accurate_id is False:
            search_results = _simple_search(query=query)
            if "error" in search_results:
                return search_results["error"]

            if not search_results:
                return "No search results found for the given query."

            search_result = search_results[0]
            place_id = search_result.get("place_id", None)
        else:
            place_id = query.strip()

        if place_id is None:
            return "Error: No place ID found in the search results."
        else:
            structured_data = _google_map_get_place_details(place_id=place_id)
            if "error" in structured_data:
                return structured_data["error"]
            return json.dumps(structured_data, ensure_ascii=False, indent=2)
    except Exception as e:
        return {"error": f"Request failed: {e}"}


@mcp.tool()
def google_map_get_place_id(query: str, max_results: int = 10) -> list[dict] | str:
    """
    Searches for places based on a query and returns a list of names and their corresponding place_ids.

    This tool is useful for getting the necessary 'place_id' required by other detailed API calls.

    Args:
        query (str): The search query (e.g., "coffee shops near me").
        max_results (int, optional): The maximum number of place IDs to return. Defaults to 10.

    Returns:
        list[dict] | str: A list of dictionaries, where each contains the 'name' and 'place_id'
                          of a search result, or an error string.
    """
    try:
        if not query:
            return "Error: Query cannot be empty."

        search_results = _simple_search(query=query, max_results=max_results)
        if "error" in search_results:
            return search_results["error"]

        final_data = []
        for result in search_results:
            final_data.append(
                {
                    "name": result.get("title", None),
                    "place_id": result.get("place_id", "Error, no place id found"),
                }
            )

        if not final_data:
            return "No place IDs found for the given query."
    except Exception as e:
        return {"error": f"Request failed: {e}"}
    return final_data


@mcp.tool()
def google_map_get_map_direction(start: str, end: str, travel_mode: int = 6) -> str:
    """
    Calculates and returns step-by-step directions between a starting point and an ending point.

    Args:
        start (str): The starting address or location name (e.g., "1st Street, London" or "Eiffel Tower").
        end (str): The destination address or location name.
        travel_mode (int, optional): The mode of transportation.
                                     Use: 6=Best (Default), 0=Driving, 9=Two-wheeler,
                                     3=Transit, 2=Walking, 1=Cycling, 4=Flight. Defaults to 6.

    Returns:
        str: A human-readable, formatted string containing the route summary and detailed directions.
    """
    if not start or not end:
        return "Error: 'start' and 'end' addresses cannot be empty."

    params = {
        "engine": "google_maps_directions",
        "start_addr": start,
        "end_addr": end,
    }
    # 6 - Best (Default)
    # 0 - Driving
    # 9 - Two-wheeler
    # 3 - Transit
    # 2 - Walking
    # 1 - Cycling
    # 4 - Flight
    try:
        if travel_mode is not None:
            params["travel_mode"] = str(travel_mode)

        data = _make_api_request(params=params)
        final_response = parse_directions(data=data)
    except Exception as e:
        return {"error": f"Request failed: {e}"}
    return final_response


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Google Map MCP Server")
    parser.add_argument(
        "transport",
        nargs="?",
        default="stdio",
        choices=["stdio", "sse", "streamable-http"],
        help="Transport type (stdio, sse, or streamable-http)",
    )
    args = parser.parse_args()

    # run mcp
    mcp.run(transport=args.transport)
