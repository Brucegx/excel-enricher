"""
Excel Enricher - Main Streamlit Application
"""
import streamlit as st
from services import data_service, prompt_service, llm_service, monitoring, sample_data_service
import io


# Page config
st.set_page_config(
    page_title="Excel Enricher",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'lab_products' not in st.session_state:
    st.session_state.lab_products = None
if 'lab_file' not in st.session_state:
    st.session_state.lab_file = None
if 'batch_products' not in st.session_state:
    st.session_state.batch_products = None
if 'batch_file' not in st.session_state:
    st.session_state.batch_file = None
if 'enriched_products' not in st.session_state:
    st.session_state.enriched_products = None
if 'using_sample_data' not in st.session_state:
    st.session_state.using_sample_data = False


def render_sidebar():
    """Render the sidebar with cost summary."""
    st.sidebar.title("📊 Excel Enricher")

    st.sidebar.info("💡 **Lab Tab**: Test prompts with sample data or upload your own\n\n"
                    "💡 **Batch Tab**: Upload a file for bulk processing")

    # Cost summary
    st.sidebar.markdown("---")
    st.sidebar.subheader("💰 This Month's Usage")

    try:
        summary = monitoring.get_monthly_summary()
        st.sidebar.metric("Total Cost", f"${summary['total_cost']:.2f}")
        st.sidebar.metric("API Calls", summary['total_calls'])

        if summary['by_model']:
            with st.sidebar.expander("By Model"):
                for model, stats in summary['by_model'].items():
                    display_name = llm_service.get_model_display_name(model)
                    st.write(f"**{display_name}**")
                    st.write(f"- Calls: {stats['calls']}")
                    st.write(f"- Cost: ${stats['cost']:.4f}")
    except Exception as e:
        st.sidebar.error(f"Error loading cost summary: {str(e)}")


def render_lab_tab():
    """Render the Lab tab for prompt testing."""
    st.header("🔬 Lab - Test & Save Prompts")

    # Data source selection
    st.subheader("Select Data Source")

    col1, col2 = st.columns([1, 1])

    with col1:
        if sample_data_service.has_sample_data():
            if st.button("📦 Use Sample Data", type="secondary", use_container_width=True):
                try:
                    st.session_state.lab_products = sample_data_service.load_sample_products()
                    st.session_state.using_sample_data = True
                    st.success(f"✅ Loaded {len(st.session_state.lab_products)} sample products")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading sample data: {str(e)}")
        else:
            st.info("No sample data available")

    with col2:
        uploaded_file = st.file_uploader(
            "📤 Or Upload Your Own Excel File",
            type=['xlsx'],
            help="Upload an Excel file with product data and embedded images",
            key="lab_file_uploader"
        )

        if uploaded_file is not None:
            # Check if new file was uploaded
            if st.session_state.lab_file is None or uploaded_file.name != st.session_state.lab_file.name:
                st.session_state.lab_file = uploaded_file
                try:
                    uploaded_file.seek(0)
                    st.session_state.lab_products = data_service.load_products(uploaded_file)
                    st.session_state.using_sample_data = False
                    st.success(f"✅ Loaded {len(st.session_state.lab_products)} products from {uploaded_file.name}")
                except Exception as e:
                    st.error(f"Error loading file: {str(e)}")
                    st.session_state.lab_products = None

    if st.session_state.lab_products is None:
        st.info("👆 Please select sample data or upload an Excel file to get started")
        return

    # Show current data source
    if st.session_state.using_sample_data:
        st.info(f"📦 Using sample data ({len(st.session_state.lab_products)} products)")
    else:
        st.info(f"📄 Using uploaded file: {st.session_state.lab_file.name if st.session_state.lab_file else 'Unknown'}")

    st.markdown("---")

    products = st.session_state.lab_products

    # 1. Select sample product
    product_options = [f"{p.item_number}" for p in products]
    selected_idx = st.selectbox(
        "1. Select Sample Product",
        range(len(products)),
        format_func=lambda i: product_options[i]
    )
    selected_product = products[selected_idx]

    # Show product image
    if selected_product.image:
        st.image(selected_product.image, caption=f"Product: {selected_product.item_number}", width=300)
    else:
        st.warning("No image found for this product")

    # Show product details
    with st.expander("Product Details"):
        st.json(selected_product.to_dict())

    st.markdown("---")

    # 2. Load or create prompt
    col1, col2 = st.columns([1, 1])

    with col1:
        available_prompts = prompt_service.list_prompts()
        prompt_to_load = st.selectbox(
            "2. Load Existing Prompt (optional)",
            [""] + available_prompts,
            help="Select a saved prompt template to load"
        )

    prompt_text = ""
    if prompt_to_load:
        try:
            prompt_text = prompt_service.get_prompt_content(prompt_to_load)
        except Exception as e:
            st.error(f"Error loading prompt: {str(e)}")

    # 3. Edit prompt
    prompt_text = st.text_area(
        "3. Edit Prompt Template",
        value=prompt_text,
        height=200,
        help="Use Jinja2 template syntax. Available variables: {{ item_number }}, {{ section }}, {{ selling_points_cn }}, etc."
    )

    # 4. Select models to test
    available_models = llm_service.get_available_models()
    model_display_names = [llm_service.get_model_display_name(m) for m in available_models]

    selected_models = st.multiselect(
        "4. Select Models to Test",
        available_models,
        format_func=lambda m: llm_service.get_model_display_name(m),
        default=[available_models[0]] if available_models else []
    )

    # 5. Run test
    if st.button("▶️ Run Test", type="primary", disabled=not prompt_text or not selected_models):
        try:
            # Render the prompt with product data
            rendered_prompt = prompt_service.render_prompt(prompt_text, selected_product)

            st.subheader("Results")

            # Create columns for side-by-side comparison
            cols = st.columns(len(selected_models))

            for idx, model in enumerate(selected_models):
                with cols[idx]:
                    with st.spinner(f"Generating with {llm_service.get_model_display_name(model)}..."):
                        try:
                            result = llm_service.generate(
                                model,
                                rendered_prompt,
                                selected_product.image
                            )

                            # Calculate and log cost
                            cost = monitoring.calculate_cost(
                                model,
                                result['input_tokens'],
                                result['output_tokens']
                            )
                            monitoring.log_usage(
                                model,
                                result['input_tokens'],
                                result['output_tokens'],
                                cost,
                                'experimental',
                                prompt_template=prompt_to_load if prompt_to_load else 'custom',
                                product_id=selected_product.item_number
                            )

                            # Display result
                            st.markdown(f"**{llm_service.get_model_display_name(model)}**")
                            st.success(result['text'])
                            st.caption(f"💰 ${cost:.4f} | 🔢 {result['input_tokens']}→{result['output_tokens']} tokens")

                        except Exception as e:
                            st.error(f"Error: {str(e)}")

        except Exception as e:
            st.error(f"Error rendering prompt: {str(e)}")

    # 6. Save prompt
    st.markdown("---")
    st.subheader("Save Prompt")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        save_category = st.selectbox(
            "Category",
            ["title", "description", "tags"],
            help="Category for this prompt"
        )

    with col2:
        save_name = st.text_input(
            "Filename (without extension)",
            placeholder="v2",
            help="Name for this prompt version (e.g., v2, experimental)"
        )

    with col3:
        save_model = st.selectbox(
            "Best Model",
            available_models,
            format_func=lambda m: llm_service.get_model_display_name(m),
            help="Which model performed best for this prompt?"
        )

    if st.button("💾 Save Prompt"):
        if not save_name:
            st.error("Please provide a filename")
        else:
            try:
                prompt_path = f"{save_category}/{save_name}.j2"
                prompt_service.save_prompt(prompt_path, prompt_text)
                prompt_service.save_prompt_config(prompt_path, save_model)
                st.success(f"✅ Saved as {prompt_path}")
            except Exception as e:
                st.error(f"Error saving prompt: {str(e)}")


def render_batch_tab():
    """Render the Batch tab for bulk processing."""
    st.header("🏭 Batch - Generate & Download")

    # File upload for batch processing
    st.subheader("1. Upload Excel File for Batch Processing")

    uploaded_file = st.file_uploader(
        "📤 Upload Excel File",
        type=['xlsx'],
        help="Upload an Excel file with product data and embedded images for batch processing",
        key="batch_file_uploader"
    )

    if uploaded_file is not None:
        # Check if new file was uploaded
        if st.session_state.batch_file is None or uploaded_file.name != st.session_state.batch_file.name:
            st.session_state.batch_file = uploaded_file
            try:
                uploaded_file.seek(0)
                st.session_state.batch_products = data_service.load_products(uploaded_file)
                st.success(f"✅ Loaded {len(st.session_state.batch_products)} products from {uploaded_file.name}")
                # Reset enriched products when new file is uploaded
                st.session_state.enriched_products = None
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")
                st.session_state.batch_products = None

    if st.session_state.batch_products is None:
        st.info("👆 Please upload an Excel file to get started")
        return

    products = st.session_state.batch_products

    st.write(f"**{len(products)} products** loaded and ready for processing")
    st.markdown("---")

    # Select prompts for each category
    st.subheader("2. Select Prompts")

    col1, col2, col3 = st.columns(3)

    with col1:
        title_prompts = prompt_service.list_prompts('title')
        selected_title = st.selectbox(
            "Title Prompt",
            title_prompts if title_prompts else ["No templates available"],
            disabled=not title_prompts
        )
        if selected_title and title_prompts:
            title_config = prompt_service.get_prompt_config(selected_title)
            if title_config:
                st.caption(f"📌 Best model: {llm_service.get_model_display_name(title_config['model'])}")

    with col2:
        desc_prompts = prompt_service.list_prompts('description')
        selected_desc = st.selectbox(
            "Description Prompt",
            desc_prompts if desc_prompts else ["No templates available"],
            disabled=not desc_prompts
        )
        if selected_desc and desc_prompts:
            desc_config = prompt_service.get_prompt_config(selected_desc)
            if desc_config:
                st.caption(f"📌 Best model: {llm_service.get_model_display_name(desc_config['model'])}")

    with col3:
        tag_prompts = prompt_service.list_prompts('tags')
        selected_tags = st.selectbox(
            "Tags Prompt",
            tag_prompts if tag_prompts else ["No templates available"],
            disabled=not tag_prompts
        )
        if selected_tags and tag_prompts:
            tags_config = prompt_service.get_prompt_config(selected_tags)
            if tags_config:
                st.caption(f"📌 Best model: {llm_service.get_model_display_name(tags_config['model'])}")

    # Run batch
    st.markdown("---")
    st.subheader("3. Run Batch Generation")

    can_run = title_prompts and selected_title and desc_prompts and selected_desc and tag_prompts and selected_tags

    if st.button("▶️ Run Batch Generation", type="primary", disabled=not can_run):
        # Load prompts and their configs
        title_template = prompt_service.get_prompt_content(selected_title)
        title_model = prompt_service.get_prompt_config(selected_title)['model']

        desc_template = prompt_service.get_prompt_content(selected_desc)
        desc_model = prompt_service.get_prompt_config(selected_desc)['model']

        tags_template = prompt_service.get_prompt_content(selected_tags)
        tags_model = prompt_service.get_prompt_config(selected_tags)['model']

        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        total_cost = 0.0

        # Process each product
        for idx, product in enumerate(products):
            status_text.text(f"Processing product {idx + 1}/{len(products)}: {product.item_number}")

            try:
                # Generate title
                title_prompt = prompt_service.render_prompt(title_template, product)
                title_result = llm_service.generate(title_model, title_prompt, product.image)
                product.generated_title = title_result['text']

                # Log title generation
                cost = monitoring.calculate_cost(title_model, title_result['input_tokens'], title_result['output_tokens'])
                total_cost += cost
                monitoring.log_usage(title_model, title_result['input_tokens'], title_result['output_tokens'],
                                   cost, 'batch', selected_title, product.item_number)

                # Generate description
                desc_prompt = prompt_service.render_prompt(desc_template, product)
                desc_result = llm_service.generate(desc_model, desc_prompt, product.image)
                product.generated_description = desc_result['text']

                # Log description generation
                cost = monitoring.calculate_cost(desc_model, desc_result['input_tokens'], desc_result['output_tokens'])
                total_cost += cost
                monitoring.log_usage(desc_model, desc_result['input_tokens'], desc_result['output_tokens'],
                                   cost, 'batch', selected_desc, product.item_number)

                # Generate tags
                tags_prompt = prompt_service.render_prompt(tags_template, product)
                tags_result = llm_service.generate(tags_model, tags_prompt, product.image)
                product.generated_tags = tags_result['text']

                # Log tags generation
                cost = monitoring.calculate_cost(tags_model, tags_result['input_tokens'], tags_result['output_tokens'])
                total_cost += cost
                monitoring.log_usage(tags_model, tags_result['input_tokens'], tags_result['output_tokens'],
                                   cost, 'batch', selected_tags, product.item_number)

            except Exception as e:
                st.error(f"Error processing {product.item_number}: {str(e)}")
                product.generated_title = "ERROR"
                product.generated_description = "ERROR"
                product.generated_tags = "ERROR"

            # Update progress
            progress_bar.progress((idx + 1) / len(products))

        st.session_state.enriched_products = products
        status_text.text("✅ Batch generation complete!")
        st.success(f"Generated content for {len(products)} products. Total cost: ${total_cost:.2f}")

    # Download button
    if st.session_state.enriched_products:
        st.markdown("---")
        st.subheader("4. Download Enriched Excel")

        try:
            # Reset file pointer for reading
            st.session_state.batch_file.seek(0)
            enriched_excel = data_service.export_enriched_excel(
                st.session_state.enriched_products,
                st.session_state.batch_file
            )

            st.download_button(
                label="⬇️ Download Enriched Excel",
                data=enriched_excel,
                file_name="enriched_products.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        except Exception as e:
            st.error(f"Error creating download: {str(e)}")


def main():
    """Main application entry point."""
    render_sidebar()

    # Main content tabs
    tab1, tab2 = st.tabs(["🔬 Lab", "🏭 Batch"])

    with tab1:
        render_lab_tab()

    with tab2:
        render_batch_tab()


if __name__ == "__main__":
    main()
