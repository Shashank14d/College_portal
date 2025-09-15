// Client-side validation and dynamic academic records list
document.addEventListener('DOMContentLoaded', () => {
	const form = document.getElementById('registrationForm');
	const list = document.getElementById('academicsList');
	const addBtn = document.getElementById('addAcademic');
	const pincodeInput = document.getElementById('pincode');
	const cityInput = document.getElementById('city');
	const stateSelect = document.getElementById('stateSelect');
	const citySelect = document.getElementById('citySelect');
	const cityManualWrapper = document.getElementById('cityManualWrapper');
	const cityManual = document.getElementById('cityManual');

	function addAcademicRow() {
		const wrapper = document.createElement('div');
		wrapper.className = 'card';
		wrapper.style.marginBottom = '12px';
		wrapper.innerHTML = `
			<label>Level
				<select name="level[]" class="level-select">
					<option value="UG">UG</option>
				</select>
			</label>
			<label>Degree
				<select name="degree[]" class="degree-select"></select>
			</label>
			<label>Institution
				<select name="institution[]" class="institution-select"></select>
			</label>
			<label class="institution-manual-wrapper" style="display:none;">Institution (type manually)
				<input type="text" class="institution-manual" placeholder="Enter institution name" />
			</label>
			<label>Year
				<select name="year[]" class="year-select"></select>
			</label>
			<label>Percentage <input type="number" step="0.01" name="percentage[]" min="0" max="100" required /></label>
		`;
		list.appendChild(wrapper);

		// populate degrees and years
		const levelSel = wrapper.querySelector('.level-select');
		const degreeSel = wrapper.querySelector('.degree-select');
		const yearSel = wrapper.querySelector('.year-select');
		const instSel = wrapper.querySelector('.institution-select');
		const instManualWrapper = wrapper.querySelector('.institution-manual-wrapper');
		const instManualInput = wrapper.querySelector('.institution-manual');

		async function loadYears() {
			try {
				const res = await fetch('/api/years/');
				const data = await res.json();
				yearSel.innerHTML = data.years.map(y => `<option value="${y}">${y}</option>`).join('');
			} catch {}
		}

		async function loadDegrees(level) {
			try {
				const res = await fetch(`/api/degrees/?level=${encodeURIComponent(level)}`);
				const data = await res.json();
				let degrees = data.degrees || [];
				if (level === 'UG' && !degrees.includes('BCA')) {
					degrees.push('BCA');
				}
				degreeSel.innerHTML = degrees.map(d => `<option value="${d}">${d}</option>`).join('');
			} catch {}
		}

		async function loadInstitutions() {
			try {
				const state = stateSelect?.value || '';
				let city = citySelect?.options[citySelect.selectedIndex]?.text || '';
				// If user selected manual city option, take typed value instead of option text
				if (citySelect && citySelect.value === '__OTHER__') {
					city = (typeof cityManual !== 'undefined' && cityManual) ? (cityManual.value || '').trim() : '';
				}
				const degree = degreeSel?.value || '';
				const level = levelSel?.value || '';

				let institutions = [];

				// 1) Try Overpass (OpenStreetMap) for universities in the selected city/state
				try {
					const overpassBodyCity = `
					[out:json][timeout:25];
					area["name"="${city.replaceAll('"', '\\"')}"]->.a;
					(
					  node["amenity"="university"](area.a);
					  way["amenity"="university"](area.a);
					  relation["amenity"="university"](area.a);
					);
					out tags;
					`;
					const resOP = await fetch('https://overpass-api.de/api/interpreter', {
						method: 'POST',
						headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
						body: overpassBodyCity
					});
					if (resOP.ok) {
						const data = await resOP.json();
						institutions = (data.elements || [])
							.map(el => (el.tags && el.tags.name) ? el.tags.name : null)
							.filter(Boolean);
					}
					// If nothing found at city level, try state area
					if ((!institutions || institutions.length === 0) && state) {
						const overpassBodyState = `
						[out:json][timeout:25];
						area["name"="${state.replaceAll('"', '\\"')}"]->.a;
						(
						  node["amenity"="university"](area.a);
						  way["amenity"="university"](area.a);
						  relation["amenity"="university"](area.a);
						);
						out tags;
						`;
						const resOPS = await fetch('https://overpass-api.de/api/interpreter', {
							method: 'POST',
							headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
							body: overpassBodyState
						});
						if (resOPS.ok) {
							const dataS = await resOPS.json();
							institutions = (dataS.elements || [])
								.map(el => (el.tags && el.tags.name) ? el.tags.name : null)
								.filter(Boolean);
						}
					}
				} catch (e) {
					// ignore and try fallbacks
				}

				// 2) Fallback: Hipolabs (broad coverage)
				if (!institutions || institutions.length === 0) {
					try {
						const resLive = await fetch('https://universities.hipolabs.com/search?country=India');
						const list = await resLive.json();
						const nState = (state || '').toLowerCase();
						const nCity = (city || '').toLowerCase();
						institutions = (list || []).filter(u => {
							const name = (u.name || '').toLowerCase();
							const prov = (u['state-province'] || '').toLowerCase();
							const okState = !nState || prov.includes(nState) || name.includes(nState);
							const okCity = !nCity || name.includes(nCity);
							return okState && okCity;
						}).map(u => u.name);
					} catch {}
				}

				// 3) Fallback: internal API (local/authoritative if present)
				if (!institutions || institutions.length === 0) {
					try {
						const params = new URLSearchParams({ state, city, degree, level });
						const res = await fetch(`/api/institutions/?${params.toString()}`);
						const data = await res.json();
						institutions = data.institutions || [];
					} catch {}
				}

				// Dedupe and build options
				institutions = Array.from(new Set(institutions)).sort();
				const options = institutions.map(n => `<option value=\"${n}\">${n}</option>`);
				options.push('<option value="Other">Other (type manually)</option>');
				instSel.innerHTML = options.join('');
			} catch {
				instSel.innerHTML = '<option value="">Select</option><option value="Other">Other (type manually)</option>';
			}
		}

		levelSel.addEventListener('change', () => loadDegrees(levelSel.value));
		loadYears();
		loadDegrees(levelSel.value);
		loadInstitutions();

		degreeSel.addEventListener('change', loadInstitutions);
		stateSelect?.addEventListener('change', loadInstitutions);
		citySelect?.addEventListener('change', loadInstitutions);
		// Also update institutions when manual city text changes
		if (typeof cityManual !== 'undefined' && cityManual) {
			let cityManualDebounce;
			cityManual.addEventListener('input', () => {
				clearTimeout(cityManualDebounce);
				cityManualDebounce = setTimeout(loadInstitutions, 300);
			});
		}

		// Toggle institution manual input when 'Other' selected
		instSel.addEventListener('change', () => {
			if (instSel.value === 'Other') {
				instManualWrapper.style.display = '';
				instManualInput.focus();
			} else {
				instManualWrapper.style.display = 'none';
			}
		});
	}

	addBtn?.addEventListener('click', addAcademicRow);
	addAcademicRow(); // add initial row

	form?.addEventListener('submit', (e) => {
		const pwd = form.querySelector('input[name="password"]').value;
		const cpwd = form.querySelector('input[name="confirm_password"]').value;
		if (pwd !== cpwd) {
			e.preventDefault();
			alert('Passwords do not match');
		}
		// compose hidden city as "City, State"
		let cityText = citySelect?.options[citySelect.selectedIndex]?.text || '';
		if (citySelect?.value === '__OTHER__') {
			cityText = cityManual?.value?.trim() || '';
		}
		const stateText = stateSelect?.options[stateSelect.selectedIndex]?.text || '';
		if (cityInput && (cityText || stateText)) {
			cityInput.value = cityText && stateText ? `${cityText}, ${stateText}` : (cityText || stateText);
		}

		// For each academic row, if institution is 'Other', inject option with manual text so it posts
		document.querySelectorAll('.institution-select').forEach((sel) => {
			const row = sel.closest('.card');
			const manual = row?.querySelector('.institution-manual');
			const wrap = row?.querySelector('.institution-manual-wrapper');
			if (sel.value === 'Other' && manual && manual.value.trim()) {
				const val = manual.value.trim();
				// create or select existing option
				let opt = Array.from(sel.options).find(o => o.value === val);
				if (!opt) {
					opt = document.createElement('option');
					opt.value = val;
					opt.textContent = val;
					sel.appendChild(opt);
				}
				sel.value = val;
				if (wrap) wrap.style.display = 'none';
			}
		});
	});

	// Pincode autofill (simple demo using postalpincode.in)
	pincodeInput?.addEventListener('blur', async () => {
		const pin = pincodeInput.value.trim();
		if (!pin) return;
		try {
			const res = await fetch(`https://api.postalpincode.in/pincode/${pin}`);
			const data = await res.json();
			const postOffice = data?.[0]?.PostOffice?.[0];
			if (postOffice) {
				// Set dropdowns from pincode response where possible
				const state = postOffice.State;
				const city = postOffice.District;
				if (stateSelect && citySelect) {
					await loadStates();
					stateSelect.value = state;
					await loadCities(state);
					const cityOption = Array.from(citySelect.options).find(o => o.text === city);
					if (cityOption) citySelect.value = cityOption.value;
				}
			}
		} catch {}
	});

	// Load states and cities
	async function loadStates() {
		const clientFallbackStates = [
			"Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
			"Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
			"Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
			"Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
			"Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
			"Uttar Pradesh", "Uttarakhand", "West Bengal"
		];
		// Immediately populate with fallback so UI is never blank
		try {
			if (stateSelect) {
				stateSelect.innerHTML = '<option value="">Select state</option>' + clientFallbackStates.map(s => `<option value="${s}">${s}</option>`).join('');
			}
		} catch {}
		try {
			const res = await fetch('https://countriesnow.space/api/v0.1/countries/states', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ country: 'India' })
			});
			if (!res.ok) throw new Error('states http ' + res.status);
			const data = await res.json();
			const apiStates = (data?.data?.states || []).map(s => s.name).filter(Boolean).sort();
			const states = apiStates.length ? apiStates : clientFallbackStates;
			stateSelect.innerHTML = '<option value="">Select state</option>' + states.map(s => `<option value="${s}">${s}</option>`).join('');
		} catch (err) {
			console.error('Failed to load states', err);
			stateSelect.innerHTML = '<option value="">Select state</option>' + clientFallbackStates.map(s => `<option value="${s}">${s}</option>`).join('');
		}
	}

	async function loadCities(state) {
		if (!state) {
			citySelect.innerHTML = '<option value="">Select city</option>';
			if (cityManualWrapper) cityManualWrapper.style.display = 'none';
			return;
		}
		const clientFallbackCities = {
			"Karnataka": ["Bengaluru", "Mysuru", "Mangaluru", "Hubballi"],
			"Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"],
			"Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem"],
			"Telangana": ["Hyderabad", "Warangal", "Nizamabad"],
			"Delhi": ["New Delhi"],
			"Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode"],
			"Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
			"Uttar Pradesh": ["Lucknow", "Kanpur", "Noida", "Varanasi"],
		};
		try {
			// Try public API first
			const resLive = await fetch('https://countriesnow.space/api/v0.1/countries/state/cities', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ country: 'India', state })
			});
			if (!resLive.ok) throw new Error('cities public http ' + resLive.status);
			const liveData = await resLive.json();
			let cities = Array.isArray(liveData.data) && liveData.data.length ? liveData.data : (clientFallbackCities[state] || []);
			if (cities.length === 0) {
				citySelect.innerHTML = '<option value="">Select city</option><option value="__OTHER__">Other (type manually)</option>';
				citySelect.value = '__OTHER__';
				if (cityManualWrapper) cityManualWrapper.style.display = '';
			} else {
				citySelect.innerHTML = '<option value="">Select city</option>' + cities.map(c => `<option value="${c}">${c}</option>`).join('') + '<option value="__OTHER__">Other (type manually)</option>';
				if (cityManualWrapper) cityManualWrapper.style.display = 'none';
			}
		} catch (err) {
			console.error('Failed to load cities (public)', err);
			try {
				// Try internal API next
				const res = await fetch(`/api/cities/?state=${encodeURIComponent(state)}`);
				const data = await res.json();
				let cities = Array.isArray(data.cities) && data.cities.length ? data.cities : (clientFallbackCities[state] || []);
				if (cities.length === 0) {
					citySelect.innerHTML = '<option value="">Select city</option><option value="__OTHER__">Other (type manually)</option>';
					citySelect.value = '__OTHER__';
					if (cityManualWrapper) cityManualWrapper.style.display = '';
				} else {
					citySelect.innerHTML = '<option value="">Select city</option>' + cities.map(c => `<option value="${c}">${c}</option>`).join('') + '<option value="__OTHER__">Other (type manually)</option>';
					if (cityManualWrapper) cityManualWrapper.style.display = 'none';
				}
			} catch (err2) {
				const cities = clientFallbackCities[state] || [];
				if (cities.length === 0) {
					citySelect.innerHTML = '<option value="">Select city</option><option value="__OTHER__">Other (type manually)</option>';
					citySelect.value = '__OTHER__';
					if (cityManualWrapper) cityManualWrapper.style.display = '';
				} else {
					citySelect.innerHTML = '<option value="">Select city</option>' + cities.map(c => `<option value="${c}">${c}</option>`).join('') + '<option value="__OTHER__">Other (type manually)</option>';
					if (cityManualWrapper) cityManualWrapper.style.display = 'none';
				}
			}
		}
	}

	citySelect?.addEventListener('change', () => {
		if (!citySelect) return;
		if (citySelect.value === '__OTHER__') {
			if (cityManualWrapper) cityManualWrapper.style.display = '';
			cityManual?.focus();
		} else {
			if (cityManualWrapper) cityManualWrapper.style.display = 'none';
		}
	});

	stateSelect?.addEventListener('change', async () => {
		// Populate cities quickly with fallback while network call happens
		await loadCities(stateSelect.value);
	});

	// Load states on startup even if city element is not yet used
	if (stateSelect) {
		loadStates();
	}
});
