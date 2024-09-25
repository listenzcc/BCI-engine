// ----------------------------------------------------------------
// Start SSVEP display
/**
 * Send start SSVEP display command
 */
function startSSVEPDisplay() {
    fetch('/startSSVEPDisplay')
    checkoutSSVEPPassedSeconds()
}

// ----------------------------------------
// ---- Append the pre designed sequence ----
function appendCueSequence() {
    let dom = document.getElementById('textareaOfCueSequence'),
        text = dom.value;
    d3.json(`appendCueSequence.json?text=${text}`).then(json => {
        console.log(json)
        d3.select('#preDesignedCueSequence').select('li').text(dom.value)
        dom.value = ''
    })
}

{
    let dom = document.getElementById('textareaOfCueSequence')
    d3.select('#preDesignedCueSequence').selectAll('li').on('click', evt => {
        dom.value = evt.target.textContent
    })
}

// ----------------------------------------------------------------
// SSVEP other display controls
{
    d3.select('#ssvepLayoutColumns4').on('click', () => {
        fetch('/ssvepLayoutColumns?columns=4')
    })
    d3.select('#ssvepLayoutColumns5').on('click', () => {
        fetch('/ssvepLayoutColumns?columns=5')
    })
    d3.select('#ssvepLayoutColumns6').on('click', () => {
        fetch('/ssvepLayoutColumns?columns=6')
    })
}

// ----------------------------------------------------------------
// SSVEP timing report
class RunningTimer {
    constructor() {
        this.timestamp = undefined // Seconds
        this.passed = undefined // Seconds
    }

    reset() {
        this.timestamp = undefined
        this.passed = undefined
    }

    update(timestamp, passed) {
        this.timestamp = timestamp
        this.passed = passed
    }

    /**
     * Guess the seconds elapsed since the last checkout.
     * @returns The seconds elapsed in higher resolution
     */
    translateToNow() {
        let
            // GetTime in milliseconds and translate it into seconds
            t = new Date().getTime() / 1000.0,
            // How long is passed
            dt = t - this.timestamp,
            // So, when is now
            seconds = dt + this.passed

        return seconds
    }
}

let rt = new RunningTimer()

/**
 * Checkout SSVEP passed seconds
 */
function checkoutSSVEPPassedSeconds() {
    fetch("checkoutPassedSeconds.json").then(response => {
        if (!response.ok) {
            // Failed checkout
            // Plot error message
            d3.select('#ssvepPassedSeconds').text('Error checkoutPassedSeconds.json')
            // Reset the timer
            rt.reset()
            throw new Error('Error checkoutPassedSeconds.json')
        }
        return response.json()
    }).then(
        obj => {
            rt.update(obj.timestamp, obj.passed)
            d3.select('#ssvepPassedSeconds').text(`${rt.passed.toFixed(2)} | ${rt.timestamp}`)
            // Call itself AGAIN in 1000 ms
            setTimeout(checkoutSSVEPPassedSeconds, 1000)
        }
    )
}

function updateBetterSSVEPPassedSeconds() {
    d3.select('#ssvepPassedSecondsBetter').text(rt.translateToNow().toFixed(2))
    // Call itself AGAIN in 100 ms
    setTimeout(updateBetterSSVEPPassedSeconds, 100)
}

updateBetterSSVEPPassedSeconds()
