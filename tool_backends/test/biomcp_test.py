import requests
import json
from datetime import datetime


def test_tool(method, params=None):
    """
    Test BioMCP tools

    Args:
        method: Tool method name
        params: Request parameters (optional)
    """
    if params is None:
        params = {}

    print(f"\nTesting tool: {method}")
    print(f"Parameters: {params}")

    try:
        headers = {
            'Content-Type': 'application/json'
        }

        # Construct request data (send parameters only)
        data = params

        # Unified tool call service
        url = f"http://localhost:30010/call_tool/{method}"

        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=300
        )

        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('status') is True:
                    print("✅ Test succeeded")
                    print(f"Response data: {json.dumps(result.get('result'), indent=2, ensure_ascii=False)[:1000]}...")
                else:
                    print(f"⚠️ Request succeeded but returned failure status: {result.get('result')}")
            except json.JSONDecodeError:
                print(f"⚠️ Response is not valid JSON format: {response.text[:200]}")
        else:
            print(f"❌ Request failed: HTTP {response.status_code}")
            print(f"Response content: {response.text[:200]}")

    except Exception as e:
        print(f"❌ Error occurred during testing: {str(e)}")


def main():
    today = datetime.now().strftime("%Y-%m-%d")

    # Select some common, easily-hittable example parameters
    example_pmid = "31452104"  # Example PMID
    example_nct = "NCT04280705"  # Example NCT ID
    # Use more stable identifiers: genomic coordinates (preferred) and rsID
    example_variant_hgvs = "chr7:g.140453136A>T"  # BRAF V600E (GRCh37)
    example_variant_rsid = "rs113488022"  # Common rsID mapping to BRAF V600E

    test_cases = [
        # Literature search and retrieval
        ("article_searcher", {"query": "BRAF mutations in melanoma"}),
        ("article_getter", {"pmid": example_pmid}),

        # Clinical trial search and itemized retrieval
        ("trial_searcher", {"query": "melanoma"}),
        ("trial_getter", {"nct_id": example_nct}),
        ("trial_protocol_getter", {"nct_id": example_nct}),
        ("trial_locations_getter", {"nct_id": example_nct}),
        ("trial_outcomes_getter", {"nct_id": example_nct}),
        ("trial_references_getter", {"nct_id": example_nct}),

        # Variant search and retrieval
        ("variant_searcher", {"query": "BRAF V600E"}),
        ("variant_getter", {"variant_id": example_variant_hgvs}),
        ("variant_getter", {"variant_id": example_variant_rsid}),
    ]

    print("Starting BioMCP tool tests...")
    print("=" * 50)

    for method, params in test_cases:
        test_tool(method, params)
        print("=" * 50)

    print("\nTests completed!")


if __name__ == "__main__":
    main()


